from datetime import datetime, timezone

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class DateTimeInput(BaseModel):
    query: str = Field(description="Any question about current date or time")


def _get_datetime(query: str) -> str:
    now = datetime.now(timezone.utc)
    return (
        f"Current UTC date: {now.strftime('%Y-%m-%d')}, "
        f"time: {now.strftime('%H:%M:%S')}, "
        f"day: {now.strftime('%A')}"
    )


datetime_tool = StructuredTool.from_function(
    func=_get_datetime,
    name="datetime",
    description="Get current date, time, or day of the week.",
    args_schema=DateTimeInput,
)