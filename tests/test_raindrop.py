import pytest
import httpx
import os

from avocet.raindrop import Raindrop
from unittest import mock

@pytest.fixture
def raindrop():
    return Raindrop()

@pytest.fixture
def mock_raindrop_env_var():
    with mock.patch.dict(os.environ, {'RAINDROP': 'RAINDROP_MOCK'}):
        yield

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

def test_getRaindropByCollectionId(httpx_mock, raindrop, mock_raindrop_env_var):
    httpx_mock.add_response(url=URL, json=RAINDROP_RESPONSE)

    result = raindrop.getRaindropBy('518084943')

    assert result.get(518084943)['excerpt'] == 'Build better apps, faster.'

def test_getCollections(raindrop, mock_raindrop_env_var):
    # Mock the httpx response
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        'items': [
            {'_id': '1', 'title': 'Collection 1', 'count': 10},
            {'_id': '2', 'title': 'Collection 2', 'count': 5},
            {'_id': '3', 'title': 'Collection 3', 'count': 3},
        ]
    }
    mock_get = mock.Mock(return_value=mock_response)

    # Patch the httpx get method with the mock
    with mock.patch('httpx.get', mock_get):
        collections = raindrop.getCollections()

        # Assert that the httpx get method was called with the correct arguments
        mock_get.assert_called_once_with("https://api.raindrop.io/rest/v1/collections", headers=raindrop.headers)

        # Assert that the collections were correctly parsed
        expected_collections = {
            'Collection 1': {'id': '1', 'count': 10, 'type': 'collections'},
            'Collection 2': {'id': '2', 'count': 5, 'type': 'collections'},
            'Collection 3': {'id': '3', 'count': 3, 'type': 'collections'},
        }
        assert collections == expected_collections

def test_getRaindropsBy(raindrop, mock_raindrop_env_var):
    # Mock the httpx response
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        'items': [
            {'_id': '1', 'title': 'Raindrop 1', 'excerpt': 'Excerpt 1', 'tags': [], 'link': 'https://example.com'},
            {'_id': '2', 'title': 'Raindrop 2', 'excerpt': 'Excerpt 2', 'tags': ['tag1', 'tag2'], 'link': 'https://example.com'},
            {'_id': '3', 'title': 'Raindrop 3', 'excerpt': 'Excerpt 3', 'tags': ['tag3'], 'link': 'https://example.com'},
        ]
    }
    mock_get = mock.Mock(return_value=mock_response)

    # Patch the httpx get method with the mock
    with mock.patch('httpx.get', mock_get):
        raindrops = raindrop.getRaindropsBy('123')

        # Assert that the httpx get method was called with the correct arguments
        mock_get.assert_called_once_with("https://api.raindrop.io/rest/v1/raindrops/123", headers=raindrop.headers)

        # Assert that the raindrops were correctly parsed
        expected_raindrops = {
            '1': {'excerpt': 'Excerpt 1', 'tags': [], 'title': 'Raindrop 1', 'link': 'https://example.com', 'type': 'collection'},
            '2': {'excerpt': 'Excerpt 2', 'tags': ['tag1', 'tag2'], 'title': 'Raindrop 2', 'link': 'https://example.com', 'type': 'collection'},
            '3': {'excerpt': 'Excerpt 3', 'tags': ['tag3'], 'title': 'Raindrop 3', 'link': 'https://example.com', 'type': 'collection'},
        }
        assert raindrops == expected_raindrops

def test_getRaindropByRaindropId(mocker, raindrop, mock_raindrop_env_var):
    # Define the mock response
    response = {'item': {'_id': '123', 'excerpt': 'test', 'tags': ['tag1', 'tag2'], 'title': 'test', 'link': 'https://test.com'}}

    # Mock the HTTP request using the response
    mocker.patch('httpx.get', return_value=mocker.Mock(json=lambda: response))

    # Call the function and check the response
    result = raindrop.getRaindropBy('123')
    assert result == {'123': {'excerpt': 'test', 'tags': ['tag1', 'tag2'], 'title': 'test', 'link': 'https://test.com', 'type': 'raindrop'}}

def test_postRaindrop(mocker, raindrop, mock_raindrop_env_var):
    mock_post = mocker.patch.object(httpx, "post")
    mock_post.return_value.json.return_value = {"success": True}
    raindrop.postRaindrop({"title": "test", "url": "http://example.com"})
    mock_post.assert_called_once_with(
        "https://api.raindrop.io/rest/v1/raindrop",
        headers=raindrop.headers,
        json={"title": "test", "url": "http://example.com"},
    )