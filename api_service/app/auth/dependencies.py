"""FastAPI authentication dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.services.api_keys import ApiKeyError, AuthorizedSubject, authenticate_api_key

bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key_subject(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthorizedSubject:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer API key required")
    try:
        return await authenticate_api_key(session, credentials.credentials)
    except ApiKeyError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key") from exc
