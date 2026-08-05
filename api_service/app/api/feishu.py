"""Trusted internal API used by the Feishu long-connection worker."""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models import FeishuActiveSession, FeishuSession, FeishuUserProfile

router = APIRouter(prefix="/internal/feishu", tags=["feishu-internal"])
PAGE_SIZE = 10


class SessionScope(BaseModel):
    application_id: uuid.UUID | None = None
    tenant_key: str = Field(min_length=1, max_length=128)
    open_id: str = Field(min_length=1, max_length=128)
    chat_id: str = Field(min_length=1, max_length=128)
    chat_type: str = Field(default="unknown", max_length=16)


class NewSessionRequest(SessionScope):
    title: str = Field(min_length=1, max_length=200)


class SessionOrdinalRequest(SessionScope):
    ordinal: int = Field(ge=1)


class UpsertUserRequest(BaseModel):
    application_id: uuid.UUID | None = None
    tenant_key: str = Field(min_length=1, max_length=128)
    open_id: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=2048)


class FeishuSessionResponse(BaseModel):
    ordinal: int
    title: str
    thread_id: str
    is_current: bool


def _require_worker_secret(value: Annotated[str | None, Header(alias="X-Feishu-Internal-Secret")] = None) -> None:
    expected = os.getenv("FEISHU_INTERNAL_AUTH_SECRET", "")
    if not expected or not value or not secrets.compare_digest(value, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid Feishu worker credential")


def _scope_filter(scope: SessionScope):
    return (
        FeishuSession.application_id == scope.application_id,
        FeishuSession.tenant_key == scope.tenant_key,
        FeishuSession.open_id == scope.open_id,
        FeishuSession.chat_id == scope.chat_id,
    )


async def _active(scope: SessionScope, session: AsyncSession) -> FeishuActiveSession | None:
    return await session.scalar(
        select(FeishuActiveSession).where(
            FeishuActiveSession.application_id == scope.application_id,
            FeishuActiveSession.tenant_key == scope.tenant_key,
            FeishuActiveSession.open_id == scope.open_id,
            FeishuActiveSession.chat_id == scope.chat_id,
        )
    )


async def _create(scope: SessionScope, title: str, session: AsyncSession) -> FeishuSession:
    max_ordinal = await session.scalar(
        select(func.coalesce(func.max(FeishuSession.ordinal), 0)).where(*_scope_filter(scope))
    )
    record = FeishuSession(
        application_id=scope.application_id,
        tenant_key=scope.tenant_key,
        open_id=scope.open_id,
        chat_id=scope.chat_id,
        chat_type=scope.chat_type,
        ordinal=int(max_ordinal or 0) + 1,
        title=title.strip(),
        thread_id=f"feishu:{scope.tenant_key}:{scope.open_id}:{scope.chat_id}:{uuid.uuid4()}",
    )
    session.add(record)
    await session.flush()
    return record


async def _set_active(scope: SessionScope, record: FeishuSession, session: AsyncSession) -> None:
    active = await _active(scope, session)
    if active is None:
        session.add(
            FeishuActiveSession(
                application_id=scope.application_id, tenant_key=scope.tenant_key, open_id=scope.open_id, chat_id=scope.chat_id, session_id=record.id
            )
        )
    else:
        active.session_id = record.id
    await session.flush()


def _response(record: FeishuSession, active: FeishuActiveSession | None) -> FeishuSessionResponse:
    return FeishuSessionResponse(
        ordinal=record.ordinal,
        title=record.title,
        thread_id=record.thread_id,
        is_current=active is not None and active.session_id == record.id,
    )


@router.post("/users/upsert", dependencies=[Depends(_require_worker_secret)])
async def upsert_user(payload: UpsertUserRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    record = await session.scalar(select(FeishuUserProfile).where(
        FeishuUserProfile.application_id == payload.application_id,
        FeishuUserProfile.tenant_key == payload.tenant_key,
        FeishuUserProfile.open_id == payload.open_id,
    ))
    if record is None:
        record = FeishuUserProfile(application_id=payload.application_id, tenant_key=payload.tenant_key, open_id=payload.open_id, display_name=payload.display_name, avatar_url=payload.avatar_url)
        session.add(record)
    else:
        record.display_name, record.avatar_url = payload.display_name, payload.avatar_url
    await session.flush()
    return {"id": str(record.id)}


@router.post("/sessions/resolve", response_model=FeishuSessionResponse, dependencies=[Depends(_require_worker_secret)])
async def resolve_session(scope: SessionScope, session: Annotated[AsyncSession, Depends(get_db_session)]) -> FeishuSessionResponse:
    """Return the selected session, creating the first default session when needed."""
    if scope.chat_type in {"p2p", "group"}:
        # Sessions created before chat_type was introduced can be safely
        # backfilled from the current Feishu event: one chat has one type.
        await session.execute(
            update(FeishuSession).where(*_scope_filter(scope)).values(chat_type=scope.chat_type)
        )
    active = await _active(scope, session)
    record = await session.get(FeishuSession, active.session_id) if active else None
    if record is None or record.is_archived:
        record = await _create(scope, "默认会话", session)
        await _set_active(scope, record, session)
        active = await _active(scope, session)
    record.last_used_at = datetime.now(UTC)
    return _response(record, active)


@router.post("/sessions/new", response_model=FeishuSessionResponse, dependencies=[Depends(_require_worker_secret)])
async def new_session(payload: NewSessionRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> FeishuSessionResponse:
    record = await _create(payload, payload.title, session)
    await _set_active(payload, record, session)
    return _response(record, await _active(payload, session))


@router.get("/sessions", response_model=list[FeishuSessionResponse], dependencies=[Depends(_require_worker_secret)])
async def list_sessions(
    application_id: uuid.UUID | None = Query(default=None),
    tenant_key: str = Query(min_length=1, max_length=128),
    open_id: str = Query(min_length=1, max_length=128),
    chat_id: str = Query(min_length=1, max_length=128),
    page: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_db_session),
) -> list[FeishuSessionResponse]:
    scope = SessionScope(application_id=application_id, tenant_key=tenant_key, open_id=open_id, chat_id=chat_id)
    active = await _active(scope, session)
    records = (
        await session.scalars(
            select(FeishuSession)
            .where(*_scope_filter(scope), FeishuSession.is_archived.is_(False))
            .order_by(FeishuSession.ordinal.desc())
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
        )
    ).all()
    return [_response(record, active) for record in records]


@router.post("/sessions/switch", response_model=FeishuSessionResponse, dependencies=[Depends(_require_worker_secret)])
async def switch_session(payload: SessionOrdinalRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> FeishuSessionResponse:
    record = await session.scalar(
        select(FeishuSession).where(*_scope_filter(payload), FeishuSession.ordinal == payload.ordinal, FeishuSession.is_archived.is_(False))
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session number does not exist")
    await _set_active(payload, record, session)
    return _response(record, await _active(payload, session))


@router.post("/sessions/archive", dependencies=[Depends(_require_worker_secret)])
async def archive_session(payload: SessionOrdinalRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    record = await session.scalar(
        select(FeishuSession).where(*_scope_filter(payload), FeishuSession.ordinal == payload.ordinal, FeishuSession.is_archived.is_(False))
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session number does not exist")
    active = await _active(payload, session)
    if active is not None and active.session_id == record.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot hide the current session")
    record.is_archived = True
    return {"status": "archived"}
