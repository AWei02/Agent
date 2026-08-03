"""Small protected administration API for roles, MCP servers, and API keys."""

from __future__ import annotations

import secrets
import os
import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db_session
from app.models import ApiAuditSession, ApiAuditTurn, ApiKey, ApiKeyRole, FeishuSession, FeishuTurn, FeishuUserProfile, FeishuUserRole, FeishuUserToolPermission, McpCatalogTool, McpServer, RbacRole, RbacRolePermission
from app.services.mcp_catalog import McpCatalogError, sync_mcp_catalog
from app.services.api_keys import ApiKeyError, AuthorizedSubject, authenticate_api_key, create_api_key, get_granted_tools
from app.web.admin_page import ADMIN_PAGE
from app.web.tracking_page import build_tracking_page
from app.web.feishu_users_page import FEISHU_USERS_PAGE

router = APIRouter(prefix="/admin", tags=["admin"])
basic_scheme = HTTPBasic()


def require_admin(credentials: Annotated[HTTPBasicCredentials, Depends(basic_scheme)]) -> None:
    settings = get_settings()
    is_valid = (
        bool(settings.admin_username and settings.admin_password)
        and secrets.compare_digest(credentials.username, settings.admin_username)
        and secrets.compare_digest(credentials.password, settings.admin_password)
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid administrator credentials")


@router.get("/feishu-users/view", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(require_admin)])
async def feishu_users_page() -> str:
    return FEISHU_USERS_PAGE


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    description: str | None = None


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    tool_ids: list[uuid.UUID] = Field(default_factory=list)


class CreateMcpServerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    url: str = Field(min_length=1, max_length=2048)
    description: str | None = None


class UpdateMcpServerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    url: str = Field(min_length=1, max_length=2048)
    description: str | None = None


class McpServerResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    description: str | None
    is_active: bool


class ToolResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    server_id: uuid.UUID


class SetRoleToolsRequest(BaseModel):
    tool_ids: list[uuid.UUID] = Field(default_factory=list)


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role_ids: list[uuid.UUID] = Field(default_factory=list)
    file_access: Literal["none", "read_only", "read_write"] = "none"
    notes: str | None = None
    expires_at: datetime | None = None
    chat_tracking: bool = False


class UpdateApiKeyRequest(BaseModel):
    role_ids: list[uuid.UUID] = Field(default_factory=list)
    file_access: Literal["none", "read_only", "read_write"]
    chat_tracking: bool | None = None


class CreateApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    file_access: str
    warning: str = "Copy api_key now. It is never stored in plaintext and cannot be shown again."


class ApiKeySummary(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    file_access: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
    role_ids: list[uuid.UUID] = Field(default_factory=list)
    chat_tracking: bool


class FeishuUserUpdateRequest(BaseModel):
    role_ids: list[uuid.UUID] = Field(default_factory=list)
    extra_tool_ids: list[uuid.UUID] = Field(default_factory=list)
    is_active: bool = True


class FeishuUserSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    open_id: str
    avatar_url: str | None
    role_ids: list[uuid.UUID]
    extra_tool_ids: list[uuid.UUID]
    effective_tools: list[dict[str, str]]
    session_count: int
    is_active: bool


class SessionVisibilityRequest(BaseModel):
    is_archived: bool


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_role(payload: CreateRoleRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> RoleResponse:
    role = RbacRole(name=payload.name, description=payload.description)
    session.add(role)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists") from exc
    return RoleResponse(id=role.id, name=role.name, description=role.description)


@router.get("/roles", response_model=list[RoleResponse], dependencies=[Depends(require_admin)])
async def list_roles(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[RoleResponse]:
    roles = (await session.scalars(select(RbacRole).where(RbacRole.is_active.is_(True)).order_by(RbacRole.name))).all()
    role_tool_rows = (await session.execute(select(RbacRolePermission.role_id, RbacRolePermission.tool_id))).all()
    tool_ids_by_role: dict[uuid.UUID, list[uuid.UUID]] = {}
    for role_id, tool_id in role_tool_rows:
        tool_ids_by_role.setdefault(role_id, []).append(tool_id)
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            tool_ids=tool_ids_by_role.get(role.id, []),
        )
        for role in roles
    ]


@router.post("/mcp-servers", response_model=McpServerResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_mcp_server(
    payload: CreateMcpServerRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> McpServerResponse:
    server = McpServer(name=payload.name, url=payload.url, description=payload.description)
    session.add(server)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MCP server name already exists") from exc
    return McpServerResponse(
        id=server.id, name=server.name, url=server.url, description=server.description, is_active=server.is_active
    )


@router.get("/mcp-servers", response_model=list[McpServerResponse], dependencies=[Depends(require_admin)])
async def list_mcp_servers(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[McpServerResponse]:
    servers = (await session.scalars(select(McpServer).order_by(McpServer.name))).all()
    return [
        McpServerResponse(
            id=server.id, name=server.name, url=server.url, description=server.description, is_active=server.is_active
        )
        for server in servers
    ]


@router.patch("/mcp-servers/{server_id}", response_model=McpServerResponse, dependencies=[Depends(require_admin)])
async def update_mcp_server(
    server_id: uuid.UUID, payload: UpdateMcpServerRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> McpServerResponse:
    server = await session.get(McpServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")
    server.name, server.url, server.description = payload.name, payload.url, payload.description
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MCP server name already exists") from exc
    return McpServerResponse(
        id=server.id, name=server.name, url=server.url, description=server.description, is_active=server.is_active
    )


async def _set_mcp_server_state(
    server_id: uuid.UUID, is_active: bool, session: AsyncSession
) -> Response:
    server = await session.get(McpServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")
    server.is_active = is_active
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mcp-servers/{server_id}/disable", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def disable_mcp_server(server_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    """Close a server immediately: it is excluded from authorization and cannot be synchronized."""
    return await _set_mcp_server_state(server_id, False, session)


@router.post("/mcp-servers/{server_id}/enable", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def enable_mcp_server(server_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    return await _set_mcp_server_state(server_id, True, session)


@router.delete("/mcp-servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_mcp_server(server_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    """Permanently remove the server and its catalog tools; role grants cascade with those tools."""
    server = await session.get(McpServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")
    await session.delete(server)
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mcp-servers/{server_id}/sync-tools", response_model=list[ToolResponse], dependencies=[Depends(require_admin)])
async def sync_server_tools(server_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[ToolResponse]:
    server = await session.get(McpServer, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")
    if not server.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MCP server is disabled; enable it before syncing")
    try:
        tools = await sync_mcp_catalog(session, server)
    except McpCatalogError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return [ToolResponse(id=tool.id, name=tool.name, description=tool.description, server_id=tool.server_id) for tool in tools]


@router.get("/mcp-tools", response_model=list[ToolResponse], dependencies=[Depends(require_admin)])
async def list_mcp_tools(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[ToolResponse]:
    tools = (
        await session.scalars(
            select(McpCatalogTool)
            .join(McpServer)
            .where(McpCatalogTool.is_active.is_(True), McpServer.is_active.is_(True))
            .order_by(McpCatalogTool.name)
        )
    ).all()
    return [ToolResponse(id=tool.id, name=tool.name, description=tool.description, server_id=tool.server_id) for tool in tools]


@router.put("/roles/{role_id}/tools", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def set_role_tools(
    role_id: uuid.UUID, payload: SetRoleToolsRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> Response:
    role = await session.get(RbacRole, role_id)
    if role is None or not role.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active role not found")
    normalized_tool_ids = list(dict.fromkeys(payload.tool_ids))
    if normalized_tool_ids:
        tools = list(
            (
                await session.scalars(
                    select(McpCatalogTool).where(McpCatalogTool.id.in_(normalized_tool_ids), McpCatalogTool.is_active.is_(True))
                )
            ).all()
        )
        if len(tools) != len(normalized_tool_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more active MCP tools do not exist")
    await session.execute(delete(RbacRolePermission).where(RbacRolePermission.role_id == role.id))
    session.add_all(RbacRolePermission(role_id=role.id, tool_id=tool_id) for tool_id in normalized_tool_ids)
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_key(
    payload: CreateApiKeyRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> CreateApiKeyResponse:
    try:
        record, raw_key = await create_api_key(
            session,
            name=payload.name,
            role_ids=payload.role_ids,
            file_access=payload.file_access,
            notes=payload.notes,
            expires_at=payload.expires_at,
            chat_tracking=payload.chat_tracking,
        )
    except ApiKeyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return CreateApiKeyResponse(id=record.id, name=record.name, api_key=raw_key, file_access=record.file_access)


@router.get("/api-keys", response_model=list[ApiKeySummary], dependencies=[Depends(require_admin)])
async def list_api_keys(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[ApiKeySummary]:
    records = (await session.scalars(select(ApiKey).order_by(ApiKey.created_at.desc()))).all()
    role_rows = (await session.execute(select(ApiKeyRole.api_key_id, ApiKeyRole.role_id))).all()
    role_ids_by_key: dict[uuid.UUID, list[uuid.UUID]] = {}
    for api_key_id, role_id in role_rows:
        role_ids_by_key.setdefault(api_key_id, []).append(role_id)
    return [
        ApiKeySummary(
            id=record.id,
            name=record.name,
            key_prefix=record.key_prefix,
            file_access=record.file_access,
            is_active=record.is_active,
            created_at=record.created_at,
            expires_at=record.expires_at,
            role_ids=role_ids_by_key.get(record.id, []),
            chat_tracking=record.chat_tracking,
        )
        for record in records
    ]


@router.patch("/api-keys/{api_key_id}", response_model=ApiKeySummary, dependencies=[Depends(require_admin)])
async def update_api_key(
    api_key_id: uuid.UUID, payload: UpdateApiKeyRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ApiKeySummary:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    normalized_role_ids = list(dict.fromkeys(payload.role_ids))
    if normalized_role_ids:
        roles = list(
            (
                await session.scalars(
                    select(RbacRole).where(RbacRole.id.in_(normalized_role_ids), RbacRole.is_active.is_(True))
                )
            ).all()
        )
        if len(roles) != len(normalized_role_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="One or more active roles do not exist")
    api_key.file_access = payload.file_access
    if payload.chat_tracking is not None:
        api_key.chat_tracking = payload.chat_tracking
    await session.execute(delete(ApiKeyRole).where(ApiKeyRole.api_key_id == api_key.id))
    session.add_all(ApiKeyRole(api_key_id=api_key.id, role_id=role_id) for role_id in normalized_role_ids)
    await session.flush()
    return ApiKeySummary(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        file_access=api_key.file_access,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        role_ids=normalized_role_ids,
        chat_tracking=api_key.chat_tracking,
    )


@router.post("/api-keys/{api_key_id}/disable", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def disable_api_key(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.is_active = False
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api-keys/{api_key_id}/enable", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def enable_api_key(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.is_active = True
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_api_key(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> Response:
    """Permanently remove a key record and its role links; it cannot be restored."""
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await session.delete(api_key)
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _feishu_summary(user: FeishuUserProfile, session: AsyncSession) -> FeishuUserSummary:
    role_ids = list((await session.scalars(select(FeishuUserRole.role_id).where(FeishuUserRole.user_id == user.id))).all())
    extra_tool_ids = list((await session.scalars(select(FeishuUserToolPermission.tool_id).where(FeishuUserToolPermission.user_id == user.id))).all())
    platform_key = os.getenv("FEISHU_PLATFORM_API_KEY", "")
    effective_tools: list[dict[str, str]] = []
    if platform_key:
        try:
            subject = await authenticate_api_key(session, platform_key)
            effective_tools = [
                {"id": str(item.server_id) + ":" + item.name, "name": item.name, "server": item.server_name}
                for item in await get_granted_tools(session, subject, feishu_user_id=user.id)
            ]
        except ApiKeyError:
            pass
    count = await session.scalar(select(func.count()).select_from(FeishuSession).where(FeishuSession.tenant_key == user.tenant_key, FeishuSession.open_id == user.open_id))
    return FeishuUserSummary(id=user.id, display_name=user.display_name, open_id=user.open_id, avatar_url=user.avatar_url, role_ids=role_ids, extra_tool_ids=extra_tool_ids, effective_tools=effective_tools, session_count=int(count or 0), is_active=user.is_active)


@router.get("/feishu-users", response_model=list[FeishuUserSummary], dependencies=[Depends(require_admin)])
async def list_feishu_users(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[FeishuUserSummary]:
    users = (await session.scalars(select(FeishuUserProfile).order_by(FeishuUserProfile.updated_at.desc()))).all()
    return [await _feishu_summary(user, session) for user in users]


@router.put("/feishu-users/{user_id}", response_model=FeishuUserSummary, dependencies=[Depends(require_admin)])
async def update_feishu_user(user_id: uuid.UUID, payload: FeishuUserUpdateRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> FeishuUserSummary:
    user = await session.get(FeishuUserProfile, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feishu user not found")
    role_ids, tool_ids = list(dict.fromkeys(payload.role_ids)), list(dict.fromkeys(payload.extra_tool_ids))
    if role_ids:
        if len((await session.scalars(select(RbacRole.id).where(RbacRole.id.in_(role_ids), RbacRole.is_active.is_(True)))).all()) != len(role_ids):
            raise HTTPException(status_code=422, detail="One or more active roles do not exist")
    if tool_ids:
        if len((await session.scalars(select(McpCatalogTool.id).where(McpCatalogTool.id.in_(tool_ids), McpCatalogTool.is_active.is_(True)))).all()) != len(tool_ids):
            raise HTTPException(status_code=422, detail="One or more active tools do not exist")
    user.is_active = payload.is_active
    await session.execute(delete(FeishuUserRole).where(FeishuUserRole.user_id == user.id))
    await session.execute(delete(FeishuUserToolPermission).where(FeishuUserToolPermission.user_id == user.id))
    session.add_all(FeishuUserRole(user_id=user.id, role_id=role_id) for role_id in role_ids)
    session.add_all(FeishuUserToolPermission(user_id=user.id, tool_id=tool_id) for tool_id in tool_ids)
    await session.flush()
    return await _feishu_summary(user, session)


@router.get("/feishu-users/{user_id}/sessions", dependencies=[Depends(require_admin)])
async def list_feishu_user_sessions(user_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[dict[str, object]]:
    user = await session.get(FeishuUserProfile, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Feishu user not found")
    records = (await session.scalars(select(FeishuSession).where(FeishuSession.tenant_key == user.tenant_key, FeishuSession.open_id == user.open_id).order_by(FeishuSession.last_used_at.desc()))).all()
    return [{"id": str(item.id), "title": item.title, "thread_id": item.thread_id, "is_archived": item.is_archived, "last_used_at": item.last_used_at.isoformat()} for item in records]


@router.get("/feishu-users/{user_id}/sessions/view", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(require_admin)])
async def feishu_user_sessions_page(user_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> str:
    user = await session.get(FeishuUserProfile, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Feishu user not found")
    records = (await session.scalars(select(FeishuSession).where(FeishuSession.tenant_key == user.tenant_key, FeishuSession.open_id == user.open_id).order_by(FeishuSession.last_used_at.desc()))).all()
    payload = [{"id": str(item.id), "thread_id": f"#{item.ordinal} {item.title}", "chat_type": item.chat_type, "is_archived": item.is_archived, "last_used_at": item.last_used_at.isoformat()} for item in records]
    turns_by_session: dict[str, list[dict[str, object]]] = {}
    if records:
        turns = (await session.scalars(select(FeishuTurn).where(FeishuTurn.session_id.in_([item.id for item in records])).order_by(FeishuTurn.created_at))).all()
        for turn in turns:
            turns_by_session.setdefault(str(turn.session_id), []).append({"messages": turn.request_messages, "response": turn.response_content, "created_at": turn.created_at.isoformat()})
    return build_tracking_page(str(user.id), payload, turns_by_session, show_feishu_chat_filter=True)


@router.get("/feishu-sessions/{session_id}/turns", dependencies=[Depends(require_admin)])
async def list_feishu_turns(session_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[dict[str, object]]:
    turns = (await session.scalars(select(FeishuTurn).where(FeishuTurn.session_id == session_id).order_by(FeishuTurn.created_at))).all()
    return [{"messages": turn.request_messages, "response": turn.response_content, "status": turn.status, "created_at": turn.created_at.isoformat()} for turn in turns]


@router.post("/feishu-sessions/{session_id}/visibility", dependencies=[Depends(require_admin)])
async def set_feishu_session_visibility(
    session_id: uuid.UUID, payload: SessionVisibilityRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> dict[str, bool]:
    record = await session.get(FeishuSession, session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feishu session not found")
    record.is_archived = payload.is_archived
    await session.flush()
    return {"is_archived": record.is_archived}


@router.get("/api-keys/{api_key_id}/sessions", dependencies=[Depends(require_admin)])
async def list_tracked_sessions(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[dict[str, object]]:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    sessions = (
        await session.scalars(
            select(ApiAuditSession)
            .where(ApiAuditSession.api_key_id == api_key.id)
            .order_by(ApiAuditSession.last_used_at.desc())
        )
    ).all()
    return [{"id": str(item.id), "thread_id": item.thread_id, "is_archived": item.is_archived, "created_at": item.created_at.isoformat(), "last_used_at": item.last_used_at.isoformat()} for item in sessions]


@router.get("/tracked-sessions/{session_id}/turns", dependencies=[Depends(require_admin)])
async def get_tracked_turns(session_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[dict[str, object]]:
    audit_session = await session.get(ApiAuditSession, session_id)
    if audit_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked session not found")
    turns = (
        await session.scalars(select(ApiAuditTurn).where(ApiAuditTurn.session_id == session_id).order_by(ApiAuditTurn.created_at))
    ).all()
    return [{"id": str(turn.id), "messages": turn.request_messages, "response": turn.response_content, "status": turn.status, "created_at": turn.created_at.isoformat()} for turn in turns]


@router.post("/tracked-sessions/{session_id}/visibility", dependencies=[Depends(require_admin)])
async def set_tracked_session_visibility(
    session_id: uuid.UUID, payload: SessionVisibilityRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> dict[str, bool]:
    record = await session.get(ApiAuditSession, session_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked session not found")
    record.is_archived = payload.is_archived
    await session.flush()
    return {"is_archived": record.is_archived}


@router.get("/api-keys/{api_key_id}/sessions/view", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(require_admin)])
async def tracked_sessions_page(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> str:
    sessions = (
        await session.scalars(
            select(ApiAuditSession).where(ApiAuditSession.api_key_id == api_key_id).order_by(ApiAuditSession.last_used_at.desc())
        )
    ).all()
    session_payload = [
        {"id": str(item.id), "thread_id": item.thread_id, "is_archived": item.is_archived, "last_used_at": item.last_used_at.isoformat()} for item in sessions
    ]
    turns_by_session: dict[str, list[dict[str, object]]] = {}
    if sessions:
        session_ids = [item.id for item in sessions]
        turns = (
            await session.scalars(select(ApiAuditTurn).where(ApiAuditTurn.session_id.in_(session_ids)).order_by(ApiAuditTurn.created_at))
        ).all()
        for turn in turns:
            turns_by_session.setdefault(str(turn.session_id), []).append(
                {"messages": turn.request_messages, "response": turn.response_content, "created_at": turn.created_at.isoformat()}
            )
    return build_tracking_page(str(api_key_id), session_payload, turns_by_session)
    return f'''<!doctype html><meta charset="utf-8"><script src="https://cdn.tailwindcss.com"></script><main class="mx-auto max-w-5xl bg-slate-950 min-h-screen p-8 text-slate-100"><a href="/admin" class="text-sm text-sky-300">← 返回 API Key 列表</a><h1 class="mt-5 text-2xl font-bold">聊天会话跟踪</h1><div id="sessions" class="mt-6 grid gap-3"></div><section id="turns" class="mt-8 space-y-4"></section><script>const esc=s=>String(s??'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]));async function load(){{const sessions=await fetch('/admin/api-keys/{api_key_id}/sessions').then(r=>r.json());document.querySelector('#sessions').innerHTML=sessions.length?sessions.map(s=>`<button onclick="showTurns('${{s.id}}')" class="rounded-xl border border-slate-700 bg-slate-900 p-4 text-left hover:border-sky-400"><b>${{esc(s.thread_id)}}</b><p class="mt-1 text-xs text-slate-400">最后使用：${{new Date(s.last_used_at).toLocaleString()}}</p></button>`).join(''):'<p class="text-slate-400">尚无已跟踪的会话。</p>'}}async function showTurns(id){{const turns=await fetch('/admin/tracked-sessions/'+id+'/turns').then(r=>r.json());document.querySelector('#turns').innerHTML=turns.map(t=>`<article class="rounded-xl border border-slate-700 bg-slate-900 p-5"><p class="text-xs text-slate-400">${{new Date(t.created_at).toLocaleString()}}</p><pre class="mt-3 whitespace-pre-wrap text-sm text-slate-200">${{esc(JSON.stringify(t.messages,null,2))}}</pre><div class="mt-4 rounded-lg bg-emerald-500/10 p-3 text-sm text-emerald-100">${{esc(t.response||'请求失败，无回复')}}</div></article>`).join('')}}load()</script></main>'''


@router.get("/api-keys/{api_key_id}/tools", dependencies=[Depends(require_admin)])
async def get_key_tools(api_key_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[dict[str, str | None]]:
    api_key = await session.get(ApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    tools = await get_granted_tools(
        session,
        AuthorizedSubject(api_key_id=api_key.id, name=api_key.name, file_access=api_key.file_access, chat_tracking=api_key.chat_tracking),
    )
    return [
        {"server_name": tool.server_name, "server_url": tool.server_url, "name": tool.name, "description": tool.description}
        for tool in tools
    ]


@router.get("", response_class=HTMLResponse, include_in_schema=False, dependencies=[Depends(require_admin)])
async def admin_page() -> str:
    """Minimal browser UI; all mutation still goes through the protected admin API."""
    return ADMIN_PAGE
    return """<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>Deep Agents 管理台</title>
<style>body{font:14px system-ui;margin:32px;max-width:1000px}input,select,button{padding:7px;margin:4px}table{border-collapse:collapse;width:100%;margin-top:16px}th,td{border:1px solid #ddd;padding:8px;text-align:left}code{word-break:break-all}.inactive{color:#888}</style>
<h1>Deep Agents 管理台</h1><p>创建 API Key 后请立即复制；系统不会保存或再次显示其明文。</p>
<form id=\"key-form\"><input id=\"name\" placeholder=\"Key 名称\" required><select id=\"file-access\"><option value=\"none\">无文件权限</option><option value=\"read_only\">只读文件</option><option value=\"read_write\">读写文件</option></select><span id=\"roles\"></span><button>新建 API Key</button></form>
<pre id=\"new-key\"></pre><h2>已有 API Key</h2><table><thead><tr><th>名称</th><th>前缀</th><th>文件权限</th><th>状态</th><th>操作</th></tr></thead><tbody id=\"keys\"></tbody></table>
<script>
const call=(path,options={})=>fetch(path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}}).then(async r=>{if(!r.ok)throw new Error(await r.text());return r.status===204?null:r.json()});
async function load(){const [roles,keys]=await Promise.all([call('/admin/roles'),call('/admin/api-keys')]);document.querySelector('#roles').innerHTML=roles.map(r=>`<label><input type="checkbox" value="${r.id}">${r.name}</label>`).join(' ');document.querySelector('#keys').innerHTML=keys.map(k=>`<tr class="${k.is_active?'':'inactive'}"><td>${k.name}</td><td><code>${k.key_prefix}…</code></td><td>${k.file_access}</td><td>${k.is_active?'启用':'已禁用'}</td><td>${k.is_active?`<button onclick="disableKey('${k.id}')">禁用</button>`:''}</td></tr>`).join('');}
async function disableKey(id){if(confirm('禁用后该 Key 将无法再调用 API，是否继续？')){await call(`/admin/api-keys/${id}/disable`,{method:'POST'});load();}}
document.querySelector('#key-form').onsubmit=async e=>{e.preventDefault();try{const role_ids=[...document.querySelectorAll('#roles input:checked')].map(x=>x.value);const result=await call('/admin/api-keys',{method:'POST',body:JSON.stringify({name:document.querySelector('#name').value,file_access:document.querySelector('#file-access').value,role_ids})});document.querySelector('#new-key').textContent='请立即保存：'+result.api_key; e.target.reset();load();}catch(error){alert(error.message)}};load();
</script></html>"""
