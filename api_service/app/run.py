"""Windows-compatible Uvicorn launcher for the PostgreSQL LangGraph saver."""

from __future__ import annotations

import asyncio
import sys

# This must run before Uvicorn creates its event loop.  psycopg async does not
# support the ProactorEventLoop selected by Uvicorn's default Windows factory.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn


def main() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, loop="none")


if __name__ == "__main__":
    main()
