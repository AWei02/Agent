"""Skill catalog validation and authorization resolution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
import re

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ApiKeyRole, FeishuUserSkillPermission, FeishuUserRole, RbacRole, RbacRoleSkill, Skill
from app.services.api_keys import AuthorizedSubject


class SkillError(ValueError):
    pass


@dataclass(frozen=True)
class GrantedSkill:
    id: uuid.UUID
    name: str
    description: str | None
    path: str


def _skill_description(skill_file: Path) -> str | None:
    """Read the optional Agent Skills frontmatter description without a YAML dependency."""
    try:
        lines = skill_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^description:\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            return match.group(1) or None
    return None


async def sync_skill_catalog(session: AsyncSession) -> list[Skill]:
    """Mirror ``AGENT_SKILLS_DIR`` into the catalog; the filesystem is authoritative."""
    root = get_settings().skills_dir
    discovered: dict[str, Path] = {}
    if root.is_dir():
        for skill_file in root.rglob("SKILL.md"):
            relative_path = skill_file.parent.relative_to(root).as_posix()
            discovered[relative_path] = skill_file

    existing = {item.path: item for item in (await session.scalars(select(Skill))).all()}
    for relative_path, skill_file in discovered.items():
        skill = existing.get(relative_path)
        if skill is None:
            # The relative path is stable and avoids collisions for nested
            # skills with the same folder name.
            skill = Skill(name=relative_path.replace("/", "__"), path=relative_path)
            session.add(skill)
        skill.is_active = True
        description = _skill_description(skill_file)
        if description:
            skill.description = description

    # Keep historical IDs and their grants, but make removed folders
    # unavailable immediately after the next refresh.
    for relative_path, skill in existing.items():
        if relative_path not in discovered:
            skill.is_active = False
    await session.flush()
    return list(
        (
            await session.scalars(select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.name))
        ).all()
    )


def resolve_skill_path(relative_path: str) -> Path:
    """Resolve a catalog path safely and ensure it is a complete Skill."""
    root = get_settings().skills_dir
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SkillError("Skill path must stay under AGENT_SKILLS_DIR") from exc
    if not candidate.is_dir() or not (candidate / "SKILL.md").is_file():
        raise SkillError("Skill directory must exist and contain SKILL.md")
    return candidate


async def get_granted_skills(
    session: AsyncSession, subject: AuthorizedSubject, *, feishu_user_id: uuid.UUID | None = None
) -> list[GrantedSkill]:
    await sync_skill_catalog(session)
    key_skill_ids = (
        select(RbacRoleSkill.skill_id)
        .join(ApiKeyRole, ApiKeyRole.role_id == RbacRoleSkill.role_id)
        .join(RbacRole, RbacRole.id == RbacRoleSkill.role_id)
        .where(ApiKeyRole.api_key_id == subject.api_key_id, RbacRole.is_active.is_(True))
    )
    skill_id_queries = [key_skill_ids]
    if feishu_user_id is not None:
        skill_id_queries.extend(
            [
                select(RbacRoleSkill.skill_id)
                .join(FeishuUserRole, FeishuUserRole.role_id == RbacRoleSkill.role_id)
                .join(RbacRole, RbacRole.id == RbacRoleSkill.role_id)
                .where(FeishuUserRole.user_id == feishu_user_id, RbacRole.is_active.is_(True)),
                select(FeishuUserSkillPermission.skill_id).where(FeishuUserSkillPermission.user_id == feishu_user_id),
            ]
        )
    rows = (
        await session.scalars(
            select(Skill).where(Skill.id.in_(union(*skill_id_queries)), Skill.is_active.is_(True)).order_by(Skill.name)
        )
    ).all()
    grants: list[GrantedSkill] = []
    for skill in rows:
        # A removed/misconfigured directory is not loaded silently. The admin
        # can see and repair it in the catalog before it affects an Agent run.
        resolve_skill_path(skill.path)
        grants.append(GrantedSkill(id=skill.id, name=skill.name, description=skill.description, path=skill.path))
    return grants
