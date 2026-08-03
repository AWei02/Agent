"""Request-scoped Deep Agent construction with only the caller's MCP tools."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.services.api_keys import AuthorizedSubject, GrantedTool
from app.services.mcp_tokens import issue_mcp_token


class AgentRuntimeError(RuntimeError):
    """An upstream model or MCP connection could not be prepared."""


def _connections_for(subject: AuthorizedSubject, tools: list[GrantedTool], context: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    tools_by_server: dict[tuple[str, str], list[GrantedTool]] = defaultdict(list)
    for tool in tools:
        tools_by_server[(tool.server_name, tool.server_url)].append(tool)

    connections: dict[str, dict[str, Any]] = {}
    for index, ((server_name, server_url), server_tools) in enumerate(tools_by_server.items(), start=1):
        connection_name = f"{server_name}-{index}"
        token = issue_mcp_token(subject, audience=server_url, tools=server_tools, context=context)
        connections[connection_name] = {
            "transport": "http",
            "url": server_url,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    return connections


async def create_request_agent(subject: AuthorizedSubject, tools: list[GrantedTool], checkpointer=None, mcp_context: dict[str, str] | None = None):
    """Build an agent for one request, making cross-request privilege leakage impossible."""
    settings = get_settings()
    if not all((settings.openai_base_url, settings.openai_api_key, settings.openai_model)):
        raise AgentRuntimeError("OPENAI_BASE_URL, OPENAI_API_KEY, and OPENAI_MODEL must be configured")

    mcp_tools = []
    if tools:
        try:
            mcp_client = MultiServerMCPClient(_connections_for(subject, tools, mcp_context), tool_name_prefix=False)
            mcp_tools = await mcp_client.get_tools()
        except Exception as exc:
            raise AgentRuntimeError("Unable to load authorized MCP tools") from exc

    model = ChatOpenAI(
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    return create_deep_agent(
        model=model,
        tools=mcp_tools,
        system_prompt=(
            "You are the Deep Agents knowledge assistant. "
            "When a knowledge-base tool is available and relevant, call it before answering. "
            "Use only the tools provided for this request. Reply in Chinese unless the user requests another language."
        ),
        # PostgreSQL-backed checkpoints are added in the next persistence milestone.
        checkpointer=checkpointer or False,
    )
