from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    create_quality_gate_node,
    create_router_node,
    create_synthesizer_node,
    create_tool_executor_node,
)
from app.agent.providers import get_llm
from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS


def route_after_router(state: dict) -> str:
    intent = state.get("intent", "general_chat")
    if intent in ("research", "analysis", "tool_required"):
        return "tool_executor"
    return "synthesizer"


def route_after_quality_gate(state: dict) -> str:
    if state.get("needs_more_info") and state.get("loop_count", 0) < 3:
        return "tool_executor"
    return "__end__"


def build_graph(
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    api_key: str | None = None,
    checkpointer: Any = None,
) -> Any:
    llm = get_llm(model=model, temperature=temperature, api_key=api_key)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(AgentState)

    # add the 4 nodes
    graph.add_node("router", create_router_node(llm))
    graph.add_node("tool_executor", create_tool_executor_node(llm_with_tools, ALL_TOOLS))
    graph.add_node("synthesizer", create_synthesizer_node(llm))
    graph.add_node("quality_gate", create_quality_gate_node(llm))

    # wire them up
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", route_after_router, {"tool_executor": "tool_executor", "synthesizer": "synthesizer"})
    graph.add_edge("tool_executor", "synthesizer")
    graph.add_edge("synthesizer", "quality_gate")
    graph.add_conditional_edges("quality_gate", route_after_quality_gate, {"tool_executor": "tool_executor", "__end__": END})

    return graph.compile(checkpointer=checkpointer)
