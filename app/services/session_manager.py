from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_graph
from app.agent.state import AgentState
from app.api.schemas.requests import AgentConfig
from app.core.exceptions import ProviderError, SessionNotFoundError, SessionTerminatedError

logger = logging.getLogger(__name__)


class SessionData:
    def __init__(self, session_id: str, agent_config: AgentConfig):
        self.session_id = session_id
        self.agent_config = agent_config
        self.created_at = datetime.now(timezone.utc)
        self.status = "active"
        self.message_counter = 0
        self.history: list[dict] = []


class SessionManager:
    def __init__(self):
        self.sessions: dict[str, SessionData] = {}
        self.checkpointer = MemorySaver()
        self._graphs: dict[str, Any] = {}

    def _get_or_build_graph(self, config: AgentConfig) -> Any:
        cache_key = f"{config.model}:{config.temperature}:{config.llm_api_key or 'default'}"
        if cache_key not in self._graphs:
            self._graphs[cache_key] = build_graph(
                model=config.model,
                temperature=config.temperature,
                api_key=config.llm_api_key,
                checkpointer=self.checkpointer,
            )
        return self._graphs[cache_key]

    def create_session(self, agent_config: Optional[AgentConfig] = None) -> SessionData:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        config = agent_config or AgentConfig()
        session = SessionData(session_id=session_id, agent_config=config)
        self.sessions[session_id] = session
        logger.info(f"Session created: {session_id}, model={config.model}")
        return session

    def _get_active_session(self, session_id: str) -> SessionData:
        session = self.sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"No active session found with ID '{session_id}'.")
        if session.status == "terminated":
            raise SessionTerminatedError(f"Session '{session_id}' has been terminated.")
        return session

    async def send_message(self, session_id: str, content: str, metadata: dict | None = None) -> dict:
        session = self._get_active_session(session_id)
        graph = self._get_or_build_graph(session.agent_config)

        session.message_counter += 1
        user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        assistant_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        session.history.append({"message_id": user_msg_id, "role": "user", "content": content, "created_at": now})

        start_time = time.time()
        try:
            result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=content)],
                    "session_id": session_id,
                    "intent": "general_chat",
                    "tool_calls": [],
                    "needs_more_info": False,
                    "loop_count": 0,
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "llm_calls": 0},
                },
                config={"configurable": {"thread_id": session_id}},
            )
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise ProviderError(f"Agent execution failed: {str(e)}")

        latency_ms = (time.time() - start_time) * 1000

        # grab the final assistant response
        assistant_content = ""
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                assistant_content = msg.content
                break
        if not assistant_content:
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage) and msg.content:
                    assistant_content = msg.content
                    break

        tool_calls = [{"tool_name": tc["tool_name"], "input": tc["input"], "output_summary": tc["output_summary"]} for tc in result.get("tool_calls", [])]
        usage = result.get("usage", {})

        assistant_record = {
            "message_id": assistant_msg_id, "role": "assistant", "content": assistant_content,
            "created_at": datetime.now(timezone.utc), "tool_calls": tool_calls, "usage": usage,
        }
        session.history.append(assistant_record)

        logger.info(f"Message processed in {latency_ms:.0f}ms, tools={len(tool_calls)}")

        return {
            "message_id": assistant_msg_id, "session_id": session_id, "role": "assistant",
            "content": assistant_content, "tool_calls": tool_calls, "usage": usage,
            "latency_ms": round(latency_ms, 2), "created_at": assistant_record["created_at"],
        }

    def get_history(self, session_id: str) -> dict:
        session = self._get_active_session(session_id)
        return {"session_id": session_id, "message_count": len(session.history), "messages": session.history}

    def delete_session(self, session_id: str) -> dict:
        session = self._get_active_session(session_id)
        session.status = "terminated"
        logger.info(f"Session terminated: {session_id}")
        return {"session_id": session_id, "status": "terminated", "deleted_at": datetime.now(timezone.utc)}

    def get_session(self, session_id: str) -> SessionData:
        return self._get_active_session(session_id)

    @property
    def active_session_count(self) -> int:
        return sum(1 for s in self.sessions.values() if s.status == "active")
