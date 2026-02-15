from datetime import datetime, timezone

from langchain_core.tools import tool


@tool
def datetime_tool(query: str) -> str:
    now = datetime.now(timezone.utc)
    return (
        f"Current UTC date: {now.strftime('%Y-%m-%d')}, "
        f"time: {now.strftime('%H:%M:%S')}, "
        f"day: {now.strftime('%A')}"
    )
