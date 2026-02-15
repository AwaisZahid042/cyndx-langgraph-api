import numexpr
from langchain_core.tools import tool


@tool
def calculator_tool(expression: str) -> str:

    try:
        result = numexpr.evaluate(expression).item()
        return f"{expression} = {result}"
    except Exception as e:
        return f"Could not evaluate '{expression}': {str(e)}"
