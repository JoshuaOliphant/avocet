# ABOUTME: Summary provider seam — ClaudeSummaryProvider (real) and StubSummaryProvider (tests).
# ABOUTME: Fetches a bookmark's page text and asks Claude for a concise summary, cached by the DB.
from __future__ import annotations

import os
from typing import Protocol

import httpx

from avocet.models import Raindrop

CLAUDE_MODEL = "claude-haiku-4-5"
_SYSTEM_PROMPT = (
    "You are a concise bookmarking assistant. Given the text of a web page, write a "
    "2-3 sentence summary capturing what the page is about and why someone saved it. "
    "Do not include preamble; output only the summary."
)


class SummaryProvider(Protocol):
    async def summarize(self, raindrop: Raindrop) -> str: ...


class StubSummaryProvider:
    """Deterministic, network-free provider for tests and snapshots."""

    async def summarize(self, raindrop: Raindrop) -> str:
        title = raindrop.title or "this bookmark"
        return f"Summary of {title}. A deterministic placeholder used in tests."


class ClaudeSummaryProvider:
    """Fetches page text and asks Claude (Haiku) for a concise summary."""

    def __init__(self, api_key: str | None = None) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    async def _fetch_page_text(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text[:20000]

    async def summarize(self, raindrop: Raindrop) -> str:
        page_text = ""
        if raindrop.link:
            try:
                page_text = await self._fetch_page_text(raindrop.link)
            except httpx.HTTPError:
                page_text = ""
        content = page_text or (raindrop.excerpt or raindrop.title or "")
        message = await self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Title: {raindrop.title}\n\nPage text:\n{content}",
                }
            ],
        )
        from anthropic.types import TextBlock

        return "".join(
            block.text for block in message.content if isinstance(block, TextBlock)
        ).strip()
