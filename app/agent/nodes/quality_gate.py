import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

GATE_PROMPT = """Evaluate if the assistant's response adequately answers the user's question.
Consider: completeness, accuracy, and whether more tool calls would help.
Respond with ONLY: {"sufficient": true} or {"sufficient": false}"""


def create_quality_gate_node(llm):
    async def quality_gate_node(state: AgentState) -> dict:
        loop_count = state.get("loop_count", 0) + 1

        # hard limit to prevent infinite loops
        if loop_count >= 3:
            logger.info(f"Hit max loops ({loop_count}), forcing end")
            return {"needs_more_info": False, "loop_count": loop_count}

        # skip quality check for simple chat or when no tools were used
        if state.get("intent") == "general_chat" or not state.get("tool_calls"):
            return {"needs_more_info": False, "loop_count": loop_count}

        # ask the LLM to evaluate response quality
        messages = [SystemMessage(content=GATE_PROMPT)] + state["messages"][-3:]
        response = await llm.ainvoke(messages)

        usage = state.get("usage", {})
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            usage["prompt_tokens"] = usage.get("prompt_tokens", 0) + meta.get("input_tokens", 0)
            usage["completion_tokens"] = usage.get("completion_tokens", 0) + meta.get("output_tokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            usage["llm_calls"] = usage.get("llm_calls", 0) + 1

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(content)
            sufficient = parsed.get("sufficient", True)
        except (json.JSONDecodeError, AttributeError):
            sufficient = True

        logger.info(f"Quality gate: sufficient={sufficient}, loop={loop_count}")
        return {"needs_more_info": not sufficient, "loop_count": loop_count, "usage": usage}

    return quality_gate_node
