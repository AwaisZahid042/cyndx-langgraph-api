from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.api.schemas.requests import SendMessageRequest
from app.api.schemas.responses import ErrorResponse, MessageResponse, ToolCallResponse, UsageResponse
from app.services.metrics import record_token_usage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Messages"])


@router.post("/{session_id}/messages", response_model=MessageResponse, responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def send_message(request: Request, session_id: str, body: SendMessageRequest):
    sm = request.app.state.session_manager
    result = await sm.send_message(session_id=session_id, content=body.content, metadata=body.metadata)

    # track token metrics
    usage = result.get("usage", {})
    if usage.get("total_tokens", 0) > 0:
        session = sm.get_session(session_id)
        record_token_usage(session.agent_config.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))

    return MessageResponse(
        message_id=result["message_id"], session_id=result["session_id"], role=result["role"],
        content=result["content"], tool_calls=[ToolCallResponse(**tc) for tc in result.get("tool_calls", [])],
        usage=UsageResponse(**result.get("usage", {})), latency_ms=result["latency_ms"], created_at=result["created_at"],
    )


@router.post("/{session_id}/messages/stream", responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
async def send_message_stream(request: Request, session_id: str, body: SendMessageRequest):
    """SSE streaming endpoint — tokens sent in real-time as the agent generates them."""
    sm = request.app.state.session_manager
    session = sm._get_active_session(session_id)
    graph = sm._get_or_build_graph(session.agent_config)

    async def event_stream():
        start = time.time()
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        full_content = ""
        all_tool_calls = []

        session.history.append({"message_id": f"msg_{uuid.uuid4().hex[:8]}", "role": "user", "content": body.content, "created_at": datetime.now(timezone.utc)})

        yield f"data: {json.dumps({'event': 'start', 'message_id': msg_id})}\n\n"

        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=body.content)], "session_id": session_id, "intent": "general_chat",
                 "tool_calls": [], "needs_more_info": False, "loop_count": 0,
                 "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "llm_calls": 0}},
                config={"configurable": {"thread_id": session_id}}, version="v2",
            ):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        yield f"data: {json.dumps({'event': 'token', 'content': chunk.content})}\n\n"

                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({'event': 'tool_start', 'tool_name': event.get('name', 'unknown')})}\n\n"

                elif kind == "on_tool_end":
                    output = str(event.get("data", {}).get("output", ""))
                    summary = output[:200] + "..." if len(output) > 200 else output
                    all_tool_calls.append({"tool_name": event.get("name", "unknown"), "input": {}, "output_summary": summary})
                    yield f"data: {json.dumps({'event': 'tool_end', 'tool_name': event.get('name', ''), 'output_summary': summary})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        latency_ms = (time.time() - start) * 1000
        session.history.append({"message_id": msg_id, "role": "assistant", "content": full_content, "created_at": datetime.now(timezone.utc), "tool_calls": all_tool_calls, "usage": {}})
        yield f"data: {json.dumps({'event': 'done', 'message_id': msg_id, 'latency_ms': round(latency_ms, 2)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
