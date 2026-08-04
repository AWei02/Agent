"""Discover MCP tools and mirror their public metadata into the platform catalog."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import McpCatalogTool, McpServer


class McpCatalogError(Exception):
    """Raised when a registered MCP server cannot be synchronized."""


def _issue_discovery_token(audience: str) -> str:
    from os import getenv

    secret = getenv("MCP_AUTH_SECRET", "")
    if not secret:
        raise McpCatalogError("MCP_AUTH_SECRET must be configured")
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": "platform-catalog-sync",
            "tools": ["*"],
            "iat": now,
            "exp": now + timedelta(minutes=1),
            "iss": "deep-agents-api",
            "aud": audience,
            "purpose": "catalog_discovery",
        },
        secret,
        algorithm="HS256",
    )


async def sync_mcp_catalog(session: AsyncSession, server: McpServer) -> list[McpCatalogTool]:
    """Fetch tools/list with a short-lived internal token and upsert the catalog."""
    try:
        async with Client(server.url, auth=BearerAuth(_issue_discovery_token(server.url))) as client:
            discovered_tools = await client.list_tools()
    except Exception as exc:
        raise McpCatalogError(f"Unable to discover tools from {server.url}") from exc

    existing = {
        tool.name: tool
        for tool in (
            await session.scalars(select(McpCatalogTool).where(McpCatalogTool.server_id == server.id))
        ).all()
    }
    discovered_names = {tool.name for tool in discovered_tools}
    for tool in discovered_tools:
        record = existing.get(tool.name)
        if record is None:
            record = McpCatalogTool(server_id=server.id, source="mcp", name=tool.name)
            session.add(record)
        record.description = tool.description
        record.input_schema = tool.inputSchema
        record.is_active = True

    # Removal from a server should stop new authorizations, without destroying audit-relevant catalog history.
    for name, record in existing.items():
        if name not in discovered_names:
            record.is_active = False
    await session.flush()
    return list(
        (
            await session.scalars(
                select(McpCatalogTool)
                .where(McpCatalogTool.server_id == server.id, McpCatalogTool.is_active.is_(True))
                .order_by(McpCatalogTool.name)
            )
        ).all()
    )
