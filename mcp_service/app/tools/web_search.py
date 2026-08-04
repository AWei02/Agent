"""Internet search tool with an optional Brave API and no-key fallback."""

from __future__ import annotations

import os
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx


class _DuckDuckGoResultsParser(HTMLParser):
    """Extract result links from DuckDuckGo's server-rendered HTML page."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._href: str | None = None
        self._title_parts: list[str] = []
        self._in_snippet = False
        self._snippet_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and "result__a" in (attributes.get("class", "") or ""):
            self._href = attributes.get("href")
            self._title_parts = []
        if tag in {"a", "div", "span"} and "result__snippet" in (attributes.get("class", "") or ""):
            self._in_snippet = True
            self._snippet_parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._title_parts.append(data)
        if self._in_snippet:
            self._snippet_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._in_snippet and tag in {"a", "div", "span"}:
            snippet = unescape("".join(self._snippet_parts)).strip()
            if snippet and self.results:
                self.results[-1]["snippet"] = snippet
            self._in_snippet = False
            self._snippet_parts = []
        if tag != "a" or self._href is None:
            return
        title = unescape("".join(self._title_parts)).strip()
        href = _unwrap_duckduckgo_url(self._href)
        if title and href:
            self.results.append({"title": title, "url": href})
        self._href = None
        self._title_parts = []


def _unwrap_duckduckgo_url(value: str) -> str:
    """Return the destination URL instead of DuckDuckGo's tracking redirect."""
    parsed = urlparse(value)
    uddg = parse_qs(parsed.query).get("uddg", [])
    if uddg:
        return unquote(uddg[0])
    return f"https:{value}" if value.startswith("//") else value


def _validate_query(query: str) -> str:
    normalized = " ".join(query.split())
    if not normalized:
        raise ValueError("query must not be empty")
    if len(normalized) > 500:
        raise ValueError("query must be at most 500 characters")
    return normalized


async def _brave_search(client: httpx.AsyncClient, query: str, max_results: int) -> list[dict[str, str]]:
    response = await client.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": max_results},
        headers={"Accept": "application/json", "X-Subscription-Token": os.environ["BRAVE_SEARCH_API_KEY"]},
    )
    response.raise_for_status()
    return [
        {
            "title": str(item.get("title", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "snippet": str(item.get("description", "")).strip(),
        }
        for item in response.json().get("web", {}).get("results", [])[:max_results]
        if item.get("title") and item.get("url")
    ]


async def _duckduckgo_search(client: httpx.AsyncClient, query: str, max_results: int) -> list[dict[str, str]]:
    response = await client.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query},
        headers={"User-Agent": "DeepAgents-MCP/1.0"},
    )
    response.raise_for_status()
    parser = _DuckDuckGoResultsParser()
    parser.feed(response.text)
    return parser.results[:max_results]


async def web_search(query: str, max_results: int = 5) -> dict[str, object]:
    """Search the public web and return titles, URLs, and short result snippets."""
    normalized_query = _validate_query(query)
    limit = max(1, min(max_results, 10))
    provider = "brave" if os.environ.get("BRAVE_SEARCH_API_KEY") else "duckduckgo"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True) as client:
            results = (
                await _brave_search(client, normalized_query, limit)
                if provider == "brave"
                else await _duckduckgo_search(client, normalized_query, limit)
            )
    except httpx.HTTPError as exc:
        return {"query": normalized_query, "provider": provider, "results": [], "error": f"Search failed: {exc.__class__.__name__}"}
    return {
        "query": normalized_query,
        "provider": provider,
        "results": results,
        "notice": "Search results are external sources; verify important facts before relying on them.",
    }
