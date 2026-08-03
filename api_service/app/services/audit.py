"""Opt-in API chat audit storage."""
from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ApiAuditSession, ApiAuditTurn
from app.services.api_keys import AuthorizedSubject

async def record_turn(session: AsyncSession, subject: AuthorizedSubject, thread_id: str, messages: list[dict], response: str | None, status: str) -> None:
    audit = await session.scalar(select(ApiAuditSession).where(ApiAuditSession.thread_id == thread_id))
    if audit is None:
        audit = ApiAuditSession(api_key_id=subject.api_key_id, api_key_name=subject.name, thread_id=thread_id)
        session.add(audit); await session.flush()
    audit.last_used_at = datetime.now(UTC)
    session.add(ApiAuditTurn(session_id=audit.id, request_messages=messages, response_content=response, status=status))
    await session.flush()
