"""Runtime configuration for the API service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_schema: str = "platform"
    admin_username: str = ""
    admin_password: str = ""
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = ""
    langgraph_database_url: str = ""
    langgraph_schema: str = "langgraph"
    skills_dir: Path = Path("skills")


@lru_cache
def get_settings() -> Settings:
    service_dir = Path(__file__).resolve().parents[1]
    load_dotenv(service_dir / ".env")

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "DATABASE_URL must use the asynchronous SQLAlchemy asyncpg URL, "
            "for example postgresql+asyncpg://user:password@host:5432/database."
        )

    return Settings(
        database_url=database_url,
        database_schema=os.getenv("DATABASE_SCHEMA", "platform"),
        admin_username=os.getenv("ADMIN_USERNAME", ""),
        admin_password=os.getenv("ADMIN_PASSWORD", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
        langgraph_database_url=os.getenv("LANGGRAPH_DATABASE_URL", ""),
        langgraph_schema=os.getenv("LANGGRAPH_SCHEMA", "langgraph"),
        skills_dir=Path(os.getenv("AGENT_SKILLS_DIR", str(service_dir / "skills"))).resolve(),
    )
