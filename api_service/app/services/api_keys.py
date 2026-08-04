"""API-key lifecycle and RBAC-derived MCP tool authorization."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey, ApiKeyRole, FeishuUserRole, FeishuUserToolPermission, McpCatalogTool, McpServer, RbacRole, RbacRolePermission

VALID_FILE_ACCESS = frozenset({"none", "read_only", "read_write"})


class ApiKeyError(Exception):
    """Raised when an API key is invalid or cannot be created."""


@dataclass(frozen=True)
class AuthorizedSubject:
    api_key_id: uuid.UUID
    name: str
    file_access: str
    chat_tracking: bool


@dataclass(frozen=True)
class GrantedTool:
    server_id: uuid.UUID
    server_name: str
    server_url: str
    name: str
    description: str | None


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _new_raw_key() -> str:
    return f"da_{secrets.token_urlsafe(32)}"


async def create_api_key(
    session: AsyncSession,
    *,
    name: str,
    role_ids: list[uuid.UUID],
    file_access: str = "none",
    notes: str | None = None,
    expires_at: datetime | None = None,
    chat_tracking: bool = False,
) -> tuple[ApiKey, str]:
    """Create an API key and retain its value for the protected admin console."""
    if file_access not in VALID_FILE_ACCESS:
        raise ApiKeyError("file_access must be none, read_only, or read_write")
    if expires_at is not None and expires_at.tzinfo is None:
        raise ApiKeyError("expires_at must include a timezone")

    normalized_role_ids = list(dict.fromkeys(role_ids))
    if normalized_role_ids:
        roles = list(
            (await session.scalars(select(RbacRole).where(RbacRole.id.in_(normalized_role_ids), RbacRole.is_active.is_(True)))).all()
        )
        if len(roles) != len(normalized_role_ids):
            raise ApiKeyError("one or more role IDs do not exist or are disabled")

    raw_key = _new_raw_key()
    record = ApiKey(
        name=name,
        key_prefix=raw_key[:18],
        key_hash=_hash_key(raw_key),
        key_value=raw_key,
        file_access=file_access,
        notes=notes,
        expires_at=expires_at,
        chat_tracking=chat_tracking,
    )
    session.add(record)
    await session.flush()
    session.add_all(ApiKeyRole(api_key_id=record.id, role_id=role_id) for role_id in normalized_role_ids)
    await session.flush()
    return record, raw_key


async def authenticate_api_key(session: AsyncSession, raw_key: str) -> AuthorizedSubject:
    """Validate a Bearer token without ever storing its plaintext value."""
    if not raw_key.startswith("da_"):
        raise ApiKeyError("invalid API key")

    api_key = await session.scalar(select(ApiKey).where(ApiKey.key_hash == _hash_key(raw_key)))
    now = datetime.now(UTC)
    if api_key is None or not api_key.is_active or (api_key.expires_at is not None and api_key.expires_at <= now):
        raise ApiKeyError("invalid, disabled, or expired API key")

    return AuthorizedSubject(api_key_id=api_key.id, name=api_key.name, file_access=api_key.file_access, chat_tracking=api_key.chat_tracking)


async def get_granted_tools(session: AsyncSession, subject: AuthorizedSubject, *, feishu_user_id: uuid.UUID | None = None) -> list[GrantedTool]:
    """Return API-key tools plus the selected Feishu user's incremental grants."""
    key_tool_ids = (
        select(RbacRolePermission.tool_id)
        .join(ApiKeyRole, ApiKeyRole.role_id == RbacRolePermission.role_id)
        .join(RbacRole, RbacRole.id == RbacRolePermission.role_id)
        .where(ApiKeyRole.api_key_id == subject.api_key_id, RbacRole.is_active.is_(True))
    )
    tool_id_queries = [key_tool_ids]
    if feishu_user_id is not None:
        tool_id_queries.extend(
            [
                select(RbacRolePermission.tool_id)
                .join(FeishuUserRole, FeishuUserRole.role_id == RbacRolePermission.role_id)
                .join(RbacRole, RbacRole.id == RbacRolePermission.role_id)
                .where(FeishuUserRole.user_id == feishu_user_id, RbacRole.is_active.is_(True)),
                select(FeishuUserToolPermission.tool_id).where(FeishuUserToolPermission.user_id == feishu_user_id),
            ]
        )
    allowed_ids = union(*tool_id_queries)
    query = (
        select(
            McpCatalogTool.id,
            McpServer.id,
            McpServer.name,
            McpServer.url,
            McpCatalogTool.name,
            McpCatalogTool.description,
        )
        .join(McpServer, McpServer.id == McpCatalogTool.server_id)
        .where(
            McpCatalogTool.id.in_(allowed_ids),
            McpServer.is_active.is_(True),
            McpCatalogTool.is_active.is_(True),
        )
        .order_by(McpServer.name, McpCatalogTool.name)
    )
    rows = (await session.execute(query)).all()
    return [
        GrantedTool(server_id=row[1], server_name=row[2], server_url=row[3], name=row[4], description=row[5])
        for row in rows
    ]
