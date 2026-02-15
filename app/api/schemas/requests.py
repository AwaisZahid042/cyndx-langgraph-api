from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier",
        examples=["gpt-4o-mini", "claude-3-5-haiku-20241022", "gemini-2.0-flash", "llama-3.1-8b-instant"],
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_api_key: Optional[str] = Field(
        default=None,
        description="Optional: bring your own LLM API key for this session. If omitted, uses server default.",
        examples=["sk-...", "sk-ant-...", "gsk_..."],
    )


class CreateSessionRequest(BaseModel):
    agent_config: Optional[AgentConfig] = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    metadata: Optional[dict[str, Any]] = None
