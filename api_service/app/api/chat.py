"""OpenAI-compatible non-streaming Chat Completions endpoint."""

from __future__ import annotations

import os
import secrets
import time
import uuid
import logging
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from openai import APIStatusError, RateLimitError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime import AgentRuntimeError, build_skill_files, create_request_agent
from app.auth.dependencies import get_api_key_subject
from app.db import get_db_session
from app.services.api_keys import AuthorizedSubject, get_granted_tools
from app.services.skills import SkillError, get_granted_skills
from app.services.audit import record_turn
from app.services.observability import langfuse_callbacks, observe_chat_request, record_chat_output
from app.models import FeishuSession, FeishuTurn, FeishuUserProfile

router = APIRouter(prefix="/v1", tags=["chat-completions"])
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatCompletionRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False


def _to_langchain_messages(messages: list[ChatMessage]) -> list[BaseMessage]:
    converted: list[BaseMessage] = []
    for message in messages:
        if message.role == "system":
            converted.append(SystemMessage(content=message.content))
        elif message.role == "assistant":
            converted.append(AIMessage(content=message.content))
        else:
            converted.append(HumanMessage(content=message.content))
    return converted


def _content_as_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content)


async def _feishu_user(request: Request, session: AsyncSession) -> FeishuUserProfile | None:
    tenant_key, open_id = request.headers.get("X-Feishu-Tenant-Key"), request.headers.get("X-Feishu-Open-Id")
    if not tenant_key and not open_id:
        return None
    secret = request.headers.get("X-Feishu-Internal-Secret", "")
    expected = os.getenv("FEISHU_INTERNAL_AUTH_SECRET", "")
    if not tenant_key or not open_id or not expected or not secrets.compare_digest(secret, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid Feishu worker identity")
    profile = await session.scalar(select(FeishuUserProfile).where(FeishuUserProfile.tenant_key == tenant_key, FeishuUserProfile.open_id == open_id))
    if profile is None or not profile.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Feishu user is disabled or not registered")
    return profile


@router.post("/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
    subject: Annotated[AuthorizedSubject, Depends(get_api_key_subject)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    thread_id: Annotated[str | None, Header(alias="X-DeepAgents-Thread-Id")] = None,
) -> dict[str, object]:
    if payload.stream:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Streaming is not implemented yet")

    feishu_user = await _feishu_user(request, session)
    granted_tools = await get_granted_tools(session, subject, feishu_user_id=feishu_user.id if feishu_user else None)
    try:
        granted_skills = await get_granted_skills(session, subject, feishu_user_id=feishu_user.id if feishu_user else None)
    except SkillError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    mcp_context = None
    if feishu_user is not None:
        current_session = await session.scalar(select(FeishuSession).where(FeishuSession.thread_id == thread_id))
        if current_session is not None:
            mcp_context = {"feishu_chat_id": current_session.chat_id, "feishu_chat_type": request.headers.get("X-Feishu-Chat-Type", "unknown")}
    resolved_thread_id = f"key-{subject.api_key_id}:{thread_id}" if thread_id else f"request-{uuid.uuid4()}"
    source = "feishu" if feishu_user is not None else "api"
    trace_messages = [message.model_dump() for message in payload.messages]
    try:
        with observe_chat_request(
            user_id=feishu_user.open_id if feishu_user is not None else str(subject.api_key_id),
            session_id=resolved_thread_id,
            model=payload.model,
            source=source,
            messages=trace_messages,
        ) as observation:
            agent = await create_request_agent(
                subject,
                granted_tools,
                granted_skills,
                getattr(request.app.state, "checkpointer", None),
                mcp_context=mcp_context,
            )
            result = await agent.ainvoke(
                {
                    "messages": _to_langchain_messages(payload.messages),
                    # StateBackend is request/thread scoped.  The same
                    # authorized skill files are supplied on every turn so a
                    # resumed Feishu session can still read its Skill.md.
                    "files": build_skill_files(granted_skills),
                },
                config={"configurable": {"thread_id": resolved_thread_id}, "callbacks": langfuse_callbacks()},
            )
            response_messages = result.get("messages", [])
            if not response_messages:
                raise AgentRuntimeError("Agent returned no messages")
            content = _content_as_text(response_messages[-1].content)
            record_chat_output(observation, content)
    except AgentRuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except RateLimitError as exc:
        logger.warning("Model provider rate limit: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="模型服务当前限流或额度已耗尽，请稍后重试或检查模型服务配额。",
        ) from exc
    except APIStatusError as exc:
        logger.warning("Model provider rejected request: status=%s", exc.status_code)
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="模型服务当前繁忙，请稍后重试。",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"模型服务请求失败（HTTP {exc.status_code}）。",
        ) from exc
    except Exception as exc:
        logger.exception("Agent execution failed for %s request", source)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Agent execution failed") from exc

    if subject.chat_tracking:
        await record_turn(session, subject, resolved_thread_id, trace_messages, content, "completed")
    if feishu_user is not None:
        feishu_session = await session.scalar(select(FeishuSession).where(FeishuSession.thread_id == thread_id))
        if feishu_session is not None:
            feishu_session.last_used_at = datetime.now(UTC)
            session.add(FeishuTurn(session_id=feishu_session.id, request_messages=trace_messages, response_content=content, status="completed"))
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": payload.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
