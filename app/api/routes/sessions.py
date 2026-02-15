from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.schemas.requests import CreateSessionRequest
from app.api.schemas.responses import (
    AgentConfigResponse, DeleteSessionResponse, ErrorResponse,
    HistoryMessageResponse, HistoryResponse, SessionResponse,
    ToolCallResponse, UsageResponse,
)
from app.services.metrics import record_session_created, record_session_terminated

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201, responses={422: {"model": ErrorResponse}})
async def create_session(request: Request, body: CreateSessionRequest | None = None):
    sm = request.app.state.session_manager
    body = body or CreateSessionRequest()
    session = sm.create_session(agent_config=body.agent_config)
    record_session_created()

    return SessionResponse(
        session_id=session.session_id, created_at=session.created_at, status=session.status,
        agent_config=AgentConfigResponse(model=session.agent_config.model, temperature=session.agent_config.temperature),
    )


@router.get("/{session_id}/history", response_model=HistoryResponse, responses={404: {"model": ErrorResponse}})
async def get_history(request: Request, session_id: str):
    history = request.app.state.session_manager.get_history(session_id)

    messages = []
    for msg in history["messages"]:
        tool_calls = [ToolCallResponse(**tc) for tc in msg["tool_calls"]] if msg.get("tool_calls") else None
        usage = UsageResponse(**msg["usage"]) if msg.get("usage") else None
        messages.append(HistoryMessageResponse(
            message_id=msg["message_id"], role=msg["role"], content=msg["content"],
            created_at=msg["created_at"], tool_calls=tool_calls, usage=usage,
        ))

    return HistoryResponse(session_id=history["session_id"], message_count=history["message_count"], messages=messages)


@router.delete("/{session_id}", response_model=DeleteSessionResponse, responses={404: {"model": ErrorResponse}})
async def delete_session(request: Request, session_id: str):
    result = request.app.state.session_manager.delete_session(session_id)
    record_session_terminated()
    return DeleteSessionResponse(session_id=result["session_id"], status=result["status"], deleted_at=result["deleted_at"])
