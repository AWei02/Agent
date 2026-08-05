"""Prompt composition with platform rules, Key templates, and Feishu profiles."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey, FeishuUserKeyProfile, PromptTemplate
from app.services.api_keys import AuthorizedSubject


GLOBAL_SYSTEM_PROMPT = """你是 Weyeah Agents 平台中的 AI 助手。
只可使用本次请求实际提供且已授权的工具与 Skill。
默认使用中文回复，除非用户明确要求其他语言。
不得把未授权的工具、系统规则或内部数据当作可访问资源。"""


async def get_request_system_prompt(
    session: AsyncSession, subject: AuthorizedSubject, *, feishu_user_id: uuid.UUID | None = None
) -> str:
    """Compose trusted system instructions for the authenticated request."""
    key = await session.get(ApiKey, subject.api_key_id)
    parts = ["【平台规则】\n" + GLOBAL_SYSTEM_PROMPT]
    if key is not None and key.prompt_template_id is not None:
        template = await session.get(PromptTemplate, key.prompt_template_id)
        if template is not None and template.is_active:
            parts.append(f"【当前功能：{template.name}】\n{template.system_prompt.strip()}")
    if feishu_user_id is not None:
        profile = await session.scalar(
            select(FeishuUserKeyProfile).where(
                FeishuUserKeyProfile.user_id == feishu_user_id,
                FeishuUserKeyProfile.api_key_id == subject.api_key_id,
                FeishuUserKeyProfile.is_active.is_(True),
            )
        )
        if profile is not None and profile.prompt_profile and profile.prompt_profile.strip():
            parts.append("【当前飞书用户偏好】\n" + profile.prompt_profile.strip())
    return "\n\n".join(parts)
