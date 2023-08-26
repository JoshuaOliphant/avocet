from typing import Dict
import httpx
import os
from textual import log

class RaindropAPI:

    def __init__(self) -> None:
        token = os.environ["RAINDROP"]
        self._headers = {"Authorization": f"Bearer {token}"}

    async def get_collections(self) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.raindrop.io/rest/v1/collections", headers=self._headers)
        return r.json()['items']

    async def get_raindrops_by_collection_id(self, collection_id: str, search: str = None) -> Dict:
        async with httpx.AsyncClient() as client:
            if search:
                params = {"search": search}
                r = await client.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers=self._headers, params=params)
            else:
                r = await client.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers=self._headers)
        return r.json()['items']

    async def get_raindrop_by_raindrop_id(self, raindrop_id: str) -> Dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}", headers=self._headers)
        item = r.json()['item']
        raindrop = dict()
        raindrop[item['_id']] = {
            'excerpt': item['excerpt'],
            'tags': item['tags'],
            'title': item['title'],
            'link': item['link'],
            'type': 'raindrop'
        }
        r.close()
        return raindrop

    async def post_raindrop(self, url: str, collection: str, tags: list) -> None:
        raindrop = {
            "link": url,
            "collectionId": self.collections[collection]['id'],
            "tags": tags
        }
        log(f"Posting raindrop: {raindrop}")
        async with httpx.AsyncClient() as client:
            r = await client.post("https://api.raindrop.io/rest/v1/raindrop", headers=self._headers, json=raindrop)
        log(f"Raindrop posted: {r.json()}")
        r.close()
