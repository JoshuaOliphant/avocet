import requests
import os

class Raindrop:

    def __init__(self) -> None:
       token = os.environ["RAINDROP"]
       self.headers = {"Authorization": f"Bearer {token}"}
       
    def getCollections(self):
        r = requests.get("https://api.raindrop.io/rest/v1/collections", headers = self.headers)
        return r.json()['items']

if __name__ == "__main__":
    raindrop = Raindrop()
    items = raindrop.getCollections()
    d = []
    for item in items:
        entry = {'title': item['title'], 'count': item['count']}
        d.append(entry)
    print(d)
