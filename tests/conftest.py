from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.main import create_app
from app.services.session_manager import SessionManager


def make_mock_graph():
    mock = AsyncMock()

    async def mock_ainvoke(input_dict, config=None):
        user_msg = input_dict["messages"][-1].content if input_dict["messages"] else ""
        return {
            "messages": [*input_dict["messages"], AIMessage(content=f"Mock response to: {user_msg}")],
            "session_id": input_dict.get("session_id", "test"),
            "intent": "general_chat", "tool_calls": [],
            "needs_more_info": False, "loop_count": 0,
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80, "llm_calls": 1},
        }

    mock.ainvoke = mock_ainvoke

    async def mock_astream_events(input_dict, config=None, version=None):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Mock ")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="streamed ")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="response")}}

    mock.astream_events = mock_astream_events
    return mock


def make_mock_graph_with_tools():
    mock = AsyncMock()

    async def mock_ainvoke(input_dict, config=None):
        user_msg = input_dict["messages"][-1].content if input_dict["messages"] else ""
        return {
            "messages": [*input_dict["messages"], AIMessage(content=f"Research result for: {user_msg}")],
            "session_id": input_dict.get("session_id", "test"),
            "intent": "research",
            "tool_calls": [{"tool_name": "web_search", "input": {"query": user_msg}, "output_summary": "Found 3 results...", "duration_ms": 450.0}],
            "needs_more_info": False, "loop_count": 1,
            "usage": {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200, "llm_calls": 3},
        }

    mock.ainvoke = mock_ainvoke
    return mock


@pytest.fixture
def mock_graph():
    return make_mock_graph()


@pytest.fixture
def mock_graph_with_tools():
    return make_mock_graph_with_tools()


@pytest.fixture
def app(mock_graph):
    application = create_app()
    with patch("app.services.session_manager.build_graph", return_value=mock_graph):
        application.state.session_manager = SessionManager()
        yield application


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def session_id(client):
    resp = client.post("/sessions", json={})
    assert resp.status_code == 201
    return resp.json()["session_id"]
