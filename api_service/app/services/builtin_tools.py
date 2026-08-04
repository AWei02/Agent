"""Catalog entries for the Deep Agents tools governed by platform RBAC."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import McpCatalogTool


# Keep this list explicit: adding a new Deep Agents capability must be an
# intentional authorization decision, rather than silently granting it to every
# existing role after a dependency upgrade.
BUILTIN_TOOL_CATALOG: tuple[tuple[str, str], ...] = (
    ("ls", "列出 Agent 虚拟文件系统中的目录内容。"),
    ("read_file", "读取 Agent 虚拟文件系统中的文件。"),
    ("write_file", "在 Agent 虚拟文件系统中创建或覆盖文件。"),
    ("edit_file", "编辑 Agent 虚拟文件系统中的文件。"),
    ("delete", "删除 Agent 虚拟文件系统中的文件或目录。"),
    ("glob", "按模式查找 Agent 虚拟文件系统中的文件。"),
    ("grep", "搜索 Agent 虚拟文件系统中的文本。"),
    ("execute", "在配置的沙箱中执行命令；仅在沙箱后端可用。"),
    ("task", "委派隔离的子任务给 Deep Agents 子代理。"),
    ("write_todos", "维护 Deep Agents 的任务计划。"),
)

BUILTIN_TOOL_NAMES = frozenset(name for name, _ in BUILTIN_TOOL_CATALOG)


async def ensure_builtin_tool_catalog(session: AsyncSession) -> None:
    """Upsert built-in tools without changing an administrator's active flag."""
    existing = {
        tool.name: tool
        for tool in (
            await session.scalars(
                select(McpCatalogTool).where(McpCatalogTool.source == "builtin")
            )
        ).all()
    }
    for name, description in BUILTIN_TOOL_CATALOG:
        tool = existing.get(name)
        if tool is None:
            session.add(
                McpCatalogTool(
                    source="builtin",
                    name=name,
                    description=description,
                    input_schema={},
                    is_active=True,
                )
            )
        else:
            tool.description = description
            tool.input_schema = {}
