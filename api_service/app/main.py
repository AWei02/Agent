"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

# psycopg's async implementation does not support Windows ProactorEventLoop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi import Depends, FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import router as admin_router
from app.config import get_settings
from app.api.chat import router as chat_router
from app.api.feishu import router as feishu_router
from app.auth.dependencies import get_api_key_subject
from app.db import get_db_session
from app.services.api_keys import AuthorizedSubject, get_granted_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    url = settings.langgraph_database_url
    if not url:
        raise RuntimeError("LANGGRAPH_DATABASE_URL must be configured")
    separator = "&" if "?" in url else "?"
    scoped_url = f"{url}{separator}options=-csearch_path%3D{settings.langgraph_schema}"
    async with AsyncPostgresSaver.from_conn_string(scoped_url) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        yield

app = FastAPI(title="Deep Agents API", lifespan=lifespan)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(feishu_router)


@app.get("/health")
async def health(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/v1/access")
async def get_current_access(
    subject: AuthorizedSubject = Depends(get_api_key_subject), session: AsyncSession = Depends(get_db_session)
) -> dict[str, object]:
    """Temporary diagnostic endpoint; the chat endpoint will reuse this authorization path."""
    tools = await get_granted_tools(session, subject)
    return {
        "subject": {"id": str(subject.api_key_id), "name": subject.name, "file_access": subject.file_access},
        "tools": [
            {"server": tool.server_name, "url": tool.server_url, "name": tool.name, "description": tool.description}
            for tool in tools
        ],
    }
