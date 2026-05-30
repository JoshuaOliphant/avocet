# ABOUTME: Tests for the summary provider seam.
# ABOUTME: StubSummaryProvider is deterministic and never touches the network.
from avocet.models import Raindrop
from avocet.summary import StubSummaryProvider


async def test_stub_provider_is_deterministic():
    provider = StubSummaryProvider()
    raindrop = Raindrop(id=1, title="Textual", link="https://example.com")
    first = await provider.summarize(raindrop)
    second = await provider.summarize(raindrop)
    assert first == second
    assert "Textual" in first
