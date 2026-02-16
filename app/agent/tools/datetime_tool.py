from datetime import datetime, timezone

from langchain_core.tools import tool


@tool("datetime")
def datetime_tool(query: str) -> str:
    """Get current date, time, or day of the week.
    Useful when the user asks about today's date or what time it is."""
    now = datetime.now(timezone.utc)
    return (
        f"Current UTC date: {now.strftime('%Y-%m-%d')}, "
        f"time: {now.strftime('%H:%M:%S')}, "
        f"day: {now.strftime('%A')}"
    )