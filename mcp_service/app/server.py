"""FastMCP service exposing the finance, business, and HR knowledge-base tools."""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.server.middleware import AuthMiddleware

from app.auth import McpJwtVerifier, may_use_tool
from app.tools.knowledge_bases import search_business_knowledge, search_finance_knowledge, search_hr_knowledge
from app.tools.feishu_context import get_current_group_context
from app.tools.web_search import web_search

mcp = FastMCP(
    "Deep Agents Knowledge Bases",
    instructions="Fixed-response finance, business, and HR knowledge-base tools for integration testing.",
    auth=McpJwtVerifier(),
    middleware=[AuthMiddleware(auth=may_use_tool)],
)

mcp.tool(name="finance_knowledge_search", description="查询财务知识库（当前返回固定测试内容）")(search_finance_knowledge)
mcp.tool(name="business_knowledge_search", description="查询业务知识库（当前返回固定测试内容）")(search_business_knowledge)
mcp.tool(name="hr_knowledge_search", description="查询人事知识库（当前返回固定测试内容）")(search_hr_knowledge)
mcp.tool(name="get_current_group_context", description="读取当前飞书群最近消息，用于总结群聊；仅在群聊且已获授权时可用")(get_current_group_context)
mcp.tool(
    name="web_search",
    description="联网搜索公开信息，返回来源标题、链接和摘要。",
)(web_search)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.environ.get("MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("MCP_PORT", "8001")),
        path="/mcp",
    )
