from __future__ import annotations

import os
from typing import Any, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query string")


class WebSearchTool(BaseTool):

    name: str = "web_search"
    description: str = (
        "Search the web for current information. Use for recent events, "
        "company info, news, or anything needing up-to-date knowledge."
    )
    args_schema: Type[BaseModel] = WebSearchInput
    _tavily_tool: Optional[Any] = None

    def _get_tavily(self):
        if self._tavily_tool is None:
            from langchain_community.tools.tavily_search import TavilySearchResults
            self._tavily_tool = TavilySearchResults(max_results=3)
        return self._tavily_tool

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return self._get_tavily().run(query)

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        return await self._get_tavily().arun(query)


web_search_tool = WebSearchTool()
