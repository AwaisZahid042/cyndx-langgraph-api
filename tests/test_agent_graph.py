from unittest.mock import MagicMock, patch

import pytest

from app.agent.graph import build_graph, route_after_quality_gate, route_after_router
from app.agent.providers import detect_provider, get_default_model
from app.agent.state import AgentState


class TestRouterEdge:
    def test_general_chat_skips_tools(self):
        assert route_after_router({"intent": "general_chat"}) == "synthesizer"

    def test_research_uses_tools(self):
        assert route_after_router({"intent": "research"}) == "tool_executor"

    def test_analysis_uses_tools(self):
        assert route_after_router({"intent": "analysis"}) == "tool_executor"

    def test_tool_required_uses_tools(self):
        assert route_after_router({"intent": "tool_required"}) == "tool_executor"

    def test_unknown_defaults_to_synth(self):
        assert route_after_router({"intent": "unknown"}) == "synthesizer"

    def test_missing_intent_defaults(self):
        assert route_after_router({}) == "synthesizer"


class TestQualityGateEdge:
    def test_sufficient_ends(self):
        assert route_after_quality_gate({"needs_more_info": False, "loop_count": 1}) == "__end__"

    def test_needs_more_loops_back(self):
        assert route_after_quality_gate({"needs_more_info": True, "loop_count": 1}) == "tool_executor"

    def test_max_loops_forces_end(self):
        assert route_after_quality_gate({"needs_more_info": True, "loop_count": 3}) == "__end__"

    def test_default_ends(self):
        assert route_after_quality_gate({}) == "__end__"


class TestProviderDetection:
    def test_openai(self):
        assert detect_provider("gpt-4o-mini") == "openai"

    def test_anthropic(self):
        assert detect_provider("claude-3-5-haiku-20241022") == "anthropic"

    def test_google(self):
        assert detect_provider("gemini-2.0-flash") == "google"

    def test_groq(self):
        assert detect_provider("llama-3.1-8b-instant") == "groq"
        assert detect_provider("mixtral-8x7b-32768") == "groq"

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            detect_provider("unknown-model")

    def test_default_model(self):
        assert get_default_model() == "gpt-4o-mini"


class TestGraphBuild:
    @patch("app.agent.graph.get_llm")
    def test_compiles(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_get_llm.return_value = mock_llm
        assert build_graph(model="gpt-4o-mini") is not None


class TestAgentState:
    def test_has_required_fields(self):
        for field in ("messages", "session_id", "intent", "tool_calls", "needs_more_info", "loop_count", "usage"):
            assert field in AgentState.__annotations__
