from typing import Dict
import httpx
import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Collection, Base
from textual import log

class RaindropAPI:

    def __init__(self) -> None:
        token = os.environ["RAINDROP"]
        self._headers = {"Authorization": f"Bearer {token}"}

    def getCollections(self) -> Dict:
        r = httpx.get("https://api.raindrop.io/rest/v1/collections", headers=self._headers)
        return r.json()['items']

    def getRaindropsByCollectionID(self, collection_id: str) -> Dict:
        r = httpx.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers=self._headers)
        return r.json()['items']

    def getRaindropByRaindropId(self, raindrop_id: str) -> Dict:
        r = httpx.get(f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}", headers=self._headers)
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

    def postRaindrop(self, url: str, collection: str, tags: list) -> None:
        raindrop = {
            "link": url,
            "collectionId": self.collections[collection]['id'],
            "tags": tags
        }
        log(f"Posting raindrop: {raindrop}")
        r = httpx.post("https://api.raindrop.io/rest/v1/raindrop", headers=self._headers, json=raindrop)
        log(f"Raindrop posted: {r.json()}")
        r.close()


if __name__ == "__main__":
    raindrop = Raindrop()
    collections = raindrop.getRaindropsBy('30350988')
    print(collections)
