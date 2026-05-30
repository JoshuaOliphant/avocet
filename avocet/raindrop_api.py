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

    async def add_raindrop(
        self, link: str, collection_id: int, tags: list[str], title: str = ""
    ) -> dict: ...

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
            root = await client.get("/collections")
            root.raise_for_status()
            children = await client.get("/collections/childrens")
            children.raise_for_status()
        return [SYSTEM_ALL, *root.json().get("items", []), *children.json().get("items", [])]

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
                response = await client.get(f"/raindrops/{collection_id}", params=params)
                response.raise_for_status()
                batch = response.json().get("items", [])
                items.extend(batch)
                if len(batch) < PER_PAGE:
                    break
                page += 1
        return items

    async def get_raindrop(self, raindrop_id: int) -> dict:
        async with self._client() as client:
            response = await client.get(f"/raindrop/{raindrop_id}")
            response.raise_for_status()
            return response.json().get("item", {})

    async def add_raindrop(
        self, link: str, collection_id: int, tags: list[str], title: str = ""
    ) -> dict:
        payload: dict = {"link": link, "collectionId": collection_id, "tags": tags}
        if title:
            # Use the title the user typed.
            payload["title"] = title
        else:
            # Ask Raindrop to fetch the page title/excerpt itself.
            payload["pleaseParse"] = {}
        async with self._client() as client:
            response = await client.post("/raindrop", json=payload)
            response.raise_for_status()
            return response.json().get("item", {})

    async def update_raindrop(self, raindrop_id: int, fields: dict) -> dict:
        async with self._client() as client:
            response = await client.put(f"/raindrop/{raindrop_id}", json=fields)
            response.raise_for_status()
            return response.json().get("item", {})

    async def delete_raindrop(self, raindrop_id: int) -> None:
        async with self._client() as client:
            response = await client.delete(f"/raindrop/{raindrop_id}")
            response.raise_for_status()
