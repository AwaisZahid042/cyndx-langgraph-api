import logging

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

SYNTH_PROMPT = """You are a helpful AI assistant. Synthesize the conversation and any tool results 
into a clear, well-structured response. If tools were used, cite the sources naturally. 
Be concise but thorough."""


def create_synthesizer_node(llm):
    async def synthesizer_node(state: AgentState) -> dict:
        logger.info("Synthesizer generating response")
        messages = [SystemMessage(content=SYNTH_PROMPT)] + state["messages"]

        response = await llm.ainvoke(messages)

        usage = state.get("usage", {})
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            usage["prompt_tokens"] = usage.get("prompt_tokens", 0) + meta.get("input_tokens", 0)
            usage["completion_tokens"] = usage.get("completion_tokens", 0) + meta.get("output_tokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            usage["llm_calls"] = usage.get("llm_calls", 0) + 1

        return {"messages": [response], "usage": usage}

    return synthesizer_node
