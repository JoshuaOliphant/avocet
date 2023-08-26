from typing import Dict
import httpx
import os
from textual import log

class RaindropAPI:

    def __init__(self) -> None:
        token = os.environ["RAINDROP"]
        self._headers = {"Authorization": f"Bearer {token}"}
        self._client = httpx.AsyncClient()

    async def get_collections(self) -> Dict:
        r = await self._client.get("https://api.raindrop.io/rest/v1/collections", headers=self._headers)
        return r.json()['items']

    async def get_raindrops_by_collection_id(self, collection_id: str, search: str = None) -> Dict:
        if search:
            params = {"search": search}
            r = await self._client.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers=self._headers, params=params)
        else:
            r = await self._client.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers=self._headers)
        return r.json()['items']

    async def get_raindrop_by_raindrop_id(self, raindrop_id: str) -> Dict:
        r = await self._client.get(f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}", headers=self._headers)
        return r.json()['item']

    async def post_raindrop(self, url: str, collection: str, tags: list) -> None:
        raindrop = {
            "link": url,
            "collectionId": self.collections[collection]['id'],
            "tags": tags
        }
        log(f"Posting raindrop: {raindrop}")
        r = await self._client.post("https://api.raindrop.io/rest/v1/raindrop", headers=self._headers, json=raindrop)
        log(f"Raindrop posted: {r.json()}")
        r.close()
