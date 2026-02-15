import logging
import time

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def create_tool_executor_node(llm_with_tools, tools):
    tools_by_name = {t.name: t for t in tools}

    async def tool_executor_node(state: AgentState) -> dict:
        logger.info("Tool executor running")

        # ask the LLM which tools to call
        response = await llm_with_tools.ainvoke(state["messages"])

        usage = state.get("usage", {})
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            usage["prompt_tokens"] = usage.get("prompt_tokens", 0) + meta.get("input_tokens", 0)
            usage["completion_tokens"] = usage.get("completion_tokens", 0) + meta.get("output_tokens", 0)
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            usage["llm_calls"] = usage.get("llm_calls", 0) + 1

        new_messages = [response]
        tool_calls_record = list(state.get("tool_calls", []))

        # execute each tool call
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_input = tc["args"]

                logger.info(f"Calling tool: {tool_name}")
                start = time.time()

                try:
                    tool = tools_by_name[tool_name]
                    result = await tool.ainvoke(tool_input)
                    output = str(result)
                except Exception as e:
                    output = f"Tool error: {str(e)}"
                    logger.error(f"Tool {tool_name} failed: {e}")

                duration = (time.time() - start) * 1000
                summary = output[:200] + "..." if len(output) > 200 else output

                new_messages.append(
                    ToolMessage(content=output, tool_call_id=tc["id"])
                )
                tool_calls_record.append({
                    "tool_name": tool_name,
                    "input": tool_input,
                    "output_summary": summary,
                    "duration_ms": round(duration, 2),
                })

        return {
            "messages": new_messages,
            "tool_calls": tool_calls_record,
            "usage": usage,
        }

    return tool_executor_node
