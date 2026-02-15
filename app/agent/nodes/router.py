import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """You are an intent classifier. Analyze the user's message and classify it into one of these categories:

- general_chat: casual conversation, greetings, simple questions you can answer from knowledge
- research: needs web search or external data lookup
- analysis: needs calculation, data analysis, or date/time info
- tool_required: explicitly asks to use a tool

Respond with ONLY a JSON object: {"intent": "category_name"}"""


def create_router_node(llm):
    async def router_node(state: AgentState) -> dict:
        logger.info("Router node executing")
        messages = [
            SystemMessage(content=ROUTER_PROMPT),
            state["messages"][-1],
        ]

        response = await llm.ainvoke(messages)

        # track token usage
        usage = state.get("usage", {})
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            usage["prompt_tokens"] = usage.get("prompt_tokens", 0) + meta.get("input_tokens", 0)
            usage["completion_tokens"] = usage.get("completion_tokens", 0) + meta.get("output_tokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            usage["llm_calls"] = usage.get("llm_calls", 0) + 1

        # parse the intent from json response
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(content)
            intent = parsed.get("intent", "general_chat")
            if intent not in ("general_chat", "research", "analysis", "tool_required"):
                intent = "general_chat"
        except (json.JSONDecodeError, AttributeError):
            intent = "general_chat"

        logger.info(f"Classified intent: {intent}")
        return {"intent": intent, "usage": usage}

    return router_node
