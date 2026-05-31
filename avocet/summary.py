# ABOUTME: Summary provider seam — Claude and OpenAI real providers, plus a test stub.
# ABOUTME: Fetches a bookmark's page text and asks an LLM for a concise summary, cached by the DB.
from __future__ import annotations

import os
from typing import Protocol

import httpx

from avocet.models import Raindrop

CLAUDE_MODEL = "claude-haiku-4-5"
OPENAI_MODEL = "gpt-5-mini"

# Maps a provider name to the environment variable holding its API key. Used both
# to construct providers and to validate config at startup.
SUMMARY_PROVIDER_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

_SYSTEM_PROMPT = (
    "You are a concise bookmarking assistant. Given the text of a web page, write a "
    "2-3 sentence summary capturing what the page is about and why someone saved it. "
    "Do not include preamble; output only the summary."
)


class SummaryProvider(Protocol):
    async def summarize(self, raindrop: Raindrop) -> str: ...


def resolve_provider_name() -> str:
    """Pick the summary provider: an explicit AVOCET_SUMMARY_PROVIDER if set,
    otherwise auto-detect from whichever API key is present (anthropic wins if
    both). Raises ValueError for an unrecognised explicit value."""
    choice = os.environ.get("AVOCET_SUMMARY_PROVIDER", "").strip().lower()
    if choice:
        if choice not in SUMMARY_PROVIDER_KEYS:
            valid = ", ".join(sorted(SUMMARY_PROVIDER_KEYS))
            raise ValueError(f"Unknown AVOCET_SUMMARY_PROVIDER {choice!r}; use one of: {valid}.")
        return choice
    if "ANTHROPIC_API_KEY" in os.environ:
        return "anthropic"
    if "OPENAI_API_KEY" in os.environ:
        return "openai"
    return "anthropic"  # default; the missing-key check produces a clear error


def create_summary_provider() -> SummaryProvider:
    """Build the configured real summary provider. AVOCET_SUMMARY_MODEL overrides
    the provider's default model."""
    provider = resolve_provider_name()
    model = os.environ.get("AVOCET_SUMMARY_MODEL") or None
    if provider == "openai":
        return OpenAISummaryProvider(model=model)
    return ClaudeSummaryProvider(model=model)


class StubSummaryProvider:
    """Deterministic, network-free provider for tests and snapshots."""

    async def summarize(self, raindrop: Raindrop) -> str:
        title = raindrop.title or "this bookmark"
        return f"Summary of {title}. A deterministic placeholder used in tests."


class _LLMSummaryProvider:
    """Shared page-fetch and prompt orchestration for real LLM-backed providers.

    Subclasses implement `_complete(system_prompt, user_content)` for their SDK.
    """

    async def _fetch_page_text(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text[:20000]

    async def _complete(self, system_prompt: str, user_content: str) -> str:
        raise NotImplementedError

    async def summarize(self, raindrop: Raindrop) -> str:
        page_text = ""
        if raindrop.link:
            try:
                page_text = await self._fetch_page_text(raindrop.link)
            except httpx.HTTPError:
                page_text = ""
        content = page_text or (raindrop.excerpt or raindrop.title or "")
        user_content = f"Title: {raindrop.title}\n\nPage text:\n{content}"
        return (await self._complete(_SYSTEM_PROMPT, user_content)).strip()


class ClaudeSummaryProvider(_LLMSummaryProvider):
    """Summarizes via Anthropic's Claude (Haiku by default)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self._model = model or CLAUDE_MODEL

    async def _complete(self, system_prompt: str, user_content: str) -> str:
        from anthropic.types import TextBlock

        message = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            system=[
                {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(block.text for block in message.content if isinstance(block, TextBlock))


class OpenAISummaryProvider(_LLMSummaryProvider):
    """Summarizes via OpenAI's chat completions (gpt-5-mini by default)."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self._model = model or OPENAI_MODEL

    async def _complete(self, system_prompt: str, user_content: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content or ""
