"""Manual OpenAI-compatible request check for the local Deep Agents API.

Before running, create an API Key in /admin and set TEST_PLATFORM_API_KEY in
api_service/.env.  Run from api_service with:
    .venv\\Scripts\\python.exe tests\\test_openai_request.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

SERVICE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVICE_DIR / ".env")


async def main() -> None:
    api_key = os.getenv("TEST_PLATFORM_API_KEY")
    if not api_key:
        raise SystemExit(
            "Set TEST_PLATFORM_API_KEY in api_service/.env to a one-time API Key created in /admin."
        )

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("TEST_PLATFORM_BASE_URL", "http://127.0.0.1:8000/v1"),
    )
    completion = await client.chat.completions.create(
        model="deep-agents-test",
        messages=[{"role": "user", "content": "请查询财务知识库中的报销流程。"}],
    )
    message = completion.choices[0].message.content
    assert message, "The API returned an empty assistant message"
    print("OpenAI-compatible request: OK")
    print(message)


if __name__ == "__main__":
    asyncio.run(main())
