from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class ToolCallRecord(TypedDict):
    tool_name: str
    input: dict[str, Any]
    output_summary: str
    duration_ms: float


class UsageRecord(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int


class AgentState(TypedDict):
    messages: list[BaseMessage]  # uses add_messages reducer for dedup
    session_id: str
    intent: str
    tool_calls: list[ToolCallRecord]
    needs_more_info: bool
    loop_count: int
    usage: UsageRecord
