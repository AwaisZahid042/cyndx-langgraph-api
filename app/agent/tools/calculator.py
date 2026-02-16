import numexpr
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    expression: str = Field(description="Math expression to evaluate, e.g. '2 * (3 + 4)'")


def _calculate(expression: str) -> str:
    try:
        result = numexpr.evaluate(expression).item()
        return f"{expression} = {result}"
    except Exception as e:
        return f"Could not evaluate '{expression}': {str(e)}"


calculator_tool = StructuredTool.from_function(
    func=_calculate,
    name="calculator",
    description="Evaluate a math expression. Handles basic arithmetic, exponents, trig, etc.",
    args_schema=CalculatorInput,
)