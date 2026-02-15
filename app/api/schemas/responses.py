from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentConfigResponse(BaseModel):
    model: str
    temperature: float


class ToolCallResponse(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output_summary: str


class UsageResponse(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    status: str = "active"
    agent_config: AgentConfigResponse


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str = "assistant"
    content: str
    tool_calls: list[ToolCallResponse] = Field(default_factory=list)
    usage: UsageResponse = Field(default_factory=UsageResponse)
    latency_ms: float
    created_at: datetime


class HistoryMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: datetime
    tool_calls: Optional[list[ToolCallResponse]] = None
    usage: Optional[UsageResponse] = None


class HistoryResponse(BaseModel):
    session_id: str
    message_count: int
    messages: list[HistoryMessageResponse]


class DeleteSessionResponse(BaseModel):
    session_id: str
    status: str = "terminated"
    deleted_at: datetime


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    version: str
    uptime_seconds: float
    checks: dict[str, str]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
