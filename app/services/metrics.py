import time
from contextlib import contextmanager
from typing import Generator

from opentelemetry import metrics

meter = metrics.get_meter("cyndx-langgraph-api")

request_latency = meter.create_histogram(name="request_latency_ms", description="Request latency per endpoint", unit="ms")
llm_token_usage = meter.create_counter(name="llm_token_usage", description="Total LLM tokens consumed", unit="tokens")
active_sessions = meter.create_up_down_counter(name="active_sessions", description="Currently active sessions")
tool_call_duration = meter.create_histogram(name="tool_call_duration_ms", description="Tool execution duration", unit="ms")
error_counter = meter.create_counter(name="errors_total", description="Total errors by type")


def record_request_latency(endpoint: str, method: str, status_code: int, latency_ms: float):
    request_latency.record(latency_ms, attributes={"endpoint": endpoint, "method": method, "status_code": status_code})


def record_token_usage(model: str, prompt_tokens: int, completion_tokens: int):
    llm_token_usage.add(prompt_tokens, attributes={"model": model, "token_type": "prompt"})
    llm_token_usage.add(completion_tokens, attributes={"model": model, "token_type": "completion"})


def record_session_created():
    active_sessions.add(1)


def record_session_terminated():
    active_sessions.add(-1)


@contextmanager
def track_latency() -> Generator[dict, None, None]:
    ctx = {"start": time.time(), "latency_ms": 0.0}
    try:
        yield ctx
    finally:
        ctx["latency_ms"] = (time.time() - ctx["start"]) * 1000
