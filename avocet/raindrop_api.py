# ABOUTME: Async httpx client for the Raindrop.io REST API.
# ABOUTME: Paginates raindrops and merges root, nested, and the synthetic "All" collection.
from __future__ import annotations

import os
from typing import Protocol

import httpx

BASE_URL = "https://api.raindrop.io/rest/v1"
PER_PAGE = 50
SYSTEM_ALL = {"_id": 0, "title": "All", "parent": None}


class RaindropClient(Protocol):
    """The async Raindrop operations the app depends on.

    Typing the app's injected client as this protocol (rather than the concrete
    RaindropAPI) lets tests pass a structural fake without subclassing.
    """

    async def get_collections(self) -> list[dict]: ...

    async def get_raindrops_by_collection_id(
        self, collection_id: int, search: str | None = None
    ) -> list[dict]: ...

    async def get_raindrop(self, raindrop_id: int) -> dict: ...

    async def add_raindrop(self, link: str, collection_id: int, tags: list[str]) -> dict: ...

    async def update_raindrop(self, raindrop_id: int, fields: dict) -> dict: ...

    async def delete_raindrop(self, raindrop_id: int) -> None: ...


class RaindropAPI:
    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ["RAINDROP"]
        self._headers = {"Authorization": f"Bearer {self._token}"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers, base_url=BASE_URL, timeout=30.0)

    async def get_collections(self) -> list[dict]:
        async with self._client() as client:
            root = (await client.get("/collections")).json().get("items", [])
            children = (await client.get("/collections/childrens")).json().get("items", [])
        return [SYSTEM_ALL, *root, *children]

    async def get_raindrops_by_collection_id(
        self, collection_id: int, search: str | None = None
    ) -> list[dict]:
        items: list[dict] = []
        page = 0
        async with self._client() as client:
            while True:
                params: dict[str, str | int] = {"perpage": PER_PAGE, "page": page}
                if search:
                    params["search"] = search
                batch = (
                    await client.get(f"/raindrops/{collection_id}", params=params)
                ).json().get("items", [])
                items.extend(batch)
                if len(batch) < PER_PAGE:
                    break
                page += 1
        return items

    async def get_raindrop(self, raindrop_id: int) -> dict:
        async with self._client() as client:
            return (await client.get(f"/raindrop/{raindrop_id}")).json().get("item", {})

    async def add_raindrop(self, link: str, collection_id: int, tags: list[str]) -> dict:
        payload = {"link": link, "collectionId": collection_id, "pleaseParse": {}, "tags": tags}
        async with self._client() as client:
            return (await client.post("/raindrop", json=payload)).json().get("item", {})

    async def update_raindrop(self, raindrop_id: int, fields: dict) -> dict:
        async with self._client() as client:
            return (
                await client.put(f"/raindrop/{raindrop_id}", json=fields)
            ).json().get("item", {})

    async def delete_raindrop(self, raindrop_id: int) -> None:
        async with self._client() as client:
            await client.delete(f"/raindrop/{raindrop_id}")
