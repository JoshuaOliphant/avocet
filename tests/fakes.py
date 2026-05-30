# ABOUTME: Shared test double for the Raindrop API client used by interaction tests.
# ABOUTME: Implements the full RaindropClient protocol; tests subclass and override what they use.
from __future__ import annotations


class BaseFakeRaindrop:
    """A complete RaindropClient stand-in for tests.

    Every method raises by default so a test that accidentally exercises an
    un-overridden path fails loudly instead of silently returning None. Tests
    subclass this and override only the methods their scenario touches.
    """

    async def get_collections(self) -> list[dict]:
        raise NotImplementedError

    async def get_raindrops_by_collection_id(
        self, collection_id: int, search: str | None = None
    ) -> list[dict]:
        raise NotImplementedError

    async def get_raindrop(self, raindrop_id: int) -> dict:
        raise NotImplementedError

    async def add_raindrop(self, link: str, collection_id: int, tags: list[str]) -> dict:
        raise NotImplementedError

    async def update_raindrop(self, raindrop_id: int, fields: dict) -> dict:
        raise NotImplementedError

    async def delete_raindrop(self, raindrop_id: int) -> None:
        raise NotImplementedError
