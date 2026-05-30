# ABOUTME: Tests for the summary provider seam and provider selection.
# ABOUTME: StubSummaryProvider is deterministic and never touches the network.
import pytest

from avocet.models import Raindrop
from avocet.summary import (
    ClaudeSummaryProvider,
    OpenAISummaryProvider,
    StubSummaryProvider,
    create_summary_provider,
    resolve_provider_name,
)


async def test_stub_provider_is_deterministic():
    provider = StubSummaryProvider()
    raindrop = Raindrop(id=1, title="Textual", link="https://example.com")
    first = await provider.summarize(raindrop)
    second = await provider.summarize(raindrop)
    assert first == second
    assert "Textual" in first


@pytest.fixture(autouse=True)
def _clear_provider_env(monkeypatch):
    for var in (
        "AVOCET_SUMMARY_PROVIDER",
        "AVOCET_SUMMARY_MODEL",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)


def test_resolve_prefers_anthropic_when_both_keys_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert resolve_provider_name() == "anthropic"


def test_resolve_autodetects_openai_when_only_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert resolve_provider_name() == "openai"


def test_resolve_explicit_choice_overrides_autodetect(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("AVOCET_SUMMARY_PROVIDER", "openai")
    assert resolve_provider_name() == "openai"


def test_resolve_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("AVOCET_SUMMARY_PROVIDER", "grok")
    with pytest.raises(ValueError):
        resolve_provider_name()


def test_factory_builds_openai_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    assert isinstance(create_summary_provider(), OpenAISummaryProvider)


def test_factory_builds_claude_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert isinstance(create_summary_provider(), ClaudeSummaryProvider)


def test_factory_applies_model_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("AVOCET_SUMMARY_MODEL", "gpt-custom")
    provider = create_summary_provider()
    assert isinstance(provider, OpenAISummaryProvider)
    assert provider._model == "gpt-custom"
