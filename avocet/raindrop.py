from typing import Dict
import httpx
import os

class Raindrop:

    def __init__(self) -> None:
       token = os.environ["RAINDROP"]
       self.headers = {"Authorization": f"Bearer {token}"}

    def getCollections(self) -> Dict:
        r = httpx.get("https://api.raindrop.io/rest/v1/collections", headers = self.headers)
        collections = dict()
        for item in r.json()['items']:
            collections[
                item['title']] = {
                'id': item['_id'], 
                'count': item['count'],
                'type': 'collections'
            }
        r.close()
        return collections
    
    def getRaindropsBy(self, collection_id: str) -> Dict:
        r = httpx.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers = self.headers)
        raindrops = dict()
        for raindrop in r.json()['items']:
            raindrops[raindrop['_id']] = {
                'excerpt': raindrop['excerpt'],
                'tags': raindrop['tags'],
                'title': raindrop['title'],
                'link': raindrop['link'],
                'type': 'collection'
            }
        r.close()
        return raindrops
    
    def getRaindropBy(self, raindrop_id: str) -> Dict:
        r = httpx.get(f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}", headers = self.headers)
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

if __name__ == "__main__":
    raindrop = Raindrop()
    collections = raindrop.getRaindropsBy('30350988')
    print(collections)
