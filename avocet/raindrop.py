from typing import Dict
import requests
import os

class Raindrop:

    def __init__(self) -> None:
       token = os.environ["RAINDROP"]
       self.headers = {"Authorization": f"Bearer {token}"}

    def getCollections(self) -> Dict:
        r = requests.get("https://api.raindrop.io/rest/v1/collections", headers = self.headers)
        collections = dict()
        for item in r.json()['items']:
            collections[item['title']] = {'id': item['_id'], 'count': item['count']}
        r.close()
        return collections

    def getRaindropsBy(self, collection_id):
        r = requests.get(f"https://api.raindrop.io/rest/v1/raindrops/{collection_id}", headers = self.headers)
        raindrops = dict()
        for raindrop in r.json()['items']:
            raindrops[raindrop['_id']] = {
                'excerpt': raindrop['excerpt'],
                'tags': raindrop['tags'],
                'title': raindrop['title'],
                'link': raindrop['link']
            }
        r.close()
        return raindrops

if __name__ == "__main__":
    raindrop = Raindrop()
    collections = raindrop.getRaindropsBy('30350988')
    print(collections)
