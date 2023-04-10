from avocet.raindrop import Raindrop

RAINDROP_RESPONSE = {
    "result": True,
    "item": {
        "excerpt": "Build better apps, faster.",
        "note": "",
        "type": "link",
        "cover": "https://webimages.mongodb.com/_com_assets/cms/ku4ddeuf4tkw2nhdr-realm_social_share.png",
        "tags": [
            "sqlite",
            "databases"
        ],
        "removed": False,
        "_id": 518084943,
        "title": "Realm Home",
        "collection": {
            "$ref": "collections",
            "$id": 31670086,
            "$db": ""
        },
        "link": "https://realm.io/",
        "created": "2023-02-14T14:56:01.067Z",
        "lastUpdate": "2023-02-14T14:56:01.067Z",
        "important": False,
        "media": [
            {
                "type": "image",
                "link": "https://webimages.mongodb.com/_com_assets/cms/ku4ddeuf4tkw2nhdr-realm_social_share.png"
            },
            {
                "type": "image",
                "link": "https://webimages.mongodb.com/_com_assets/cms/kze3vbe452fkoetdx-PC4A7967%201.png?auto=format%252Ccompress&w=3840&quality=75"
            }
        ],
        "user": {
            "$ref": "users",
            "$id": 832571,
            "$db": ""
        },
        "highlights": [],
        "domain": "realm.io",
        "creatorRef": {
            "avatar": "",
            "_id": 832571,
            "name": "flyingyosh",
            "email": ""
        },
        "sort": 518084943,
        "collectionId": 31670086
    },
    "author": True
}
URL="https://api.raindrop.io/rest/v1/raindrop/518084943"
def test_passes(httpx_mock):
    httpx_mock.add_response(url=URL, json=RAINDROP_RESPONSE)
    rd = Raindrop()

    result = rd.getRaindropBy('518084943')

    assert result.get(518084943)['excerpt'] == 'Build better apps, faster.'
    assert True