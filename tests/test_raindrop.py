import os
import httpx
from unittest.mock import patch, Mock

from avocet.raindrop import Raindrop


class TestRaindrop:

    @patch.dict(os.environ, {"RAINDROP": "test_token"})
    @patch.object(httpx, "get")
    def test_init(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"items": [{"_id": "1", "title": "Collection 1", "count": 10},
                                                             {"_id": "2", "title": "Collection 2", "count": 20}]}
        raindrop = Raindrop()
        assert raindrop.collections == {"Collection 1": {"id": "1", "count": 10, "type": "collections"},
                                        "Collection 2": {"id": "2", "count": 20, "type": "collections"}}

    @patch.dict(os.environ, {"RAINDROP": "test_token"})
    @patch.object(httpx, "get")
    def test_get_collections(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"items": [{"_id": "1", "title": "Collection 1", "count": 10},
                                                             {"_id": "2", "title": "Collection 2", "count": 20}]}
        raindrop = Raindrop()
        collections = raindrop.getCollections()
        assert collections == {"Collection 1": {"id": "1", "count": 10, "type": "collections"},
                               "Collection 2": {"id": "2", "count": 20, "type": "collections"}}

    @patch.dict(os.environ, {"RAINDROP": "test_token"})
    @patch.object(httpx, "get")
    def test_get_raindrops_by_collection_id(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"items": [{"_id": "1", "title": "Collection 1", "count": 10},
                                                             {"_id": "2", "title": "Collection 2", "count": 20}]}
        raindrop = Raindrop()
        mock_get.return_value.json.return_value = {"items": [{"_id": "1", "title": "Raindrop 1",
                                                              "excerpt": "excerpt 1", "tags":
                                                              ["tag1", "tag2"], "link": "https://example.com/1"}]}
        raindrops = raindrop.getRaindropsByCollectionID("1")
        assert raindrops == {"1": {"excerpt": "excerpt 1", "tags": ["tag1", "tag2"], "title": "Raindrop 1",
                                   "link": "https://example.com/1", "type": "collection"}}

    @patch.dict(os.environ, {"RAINDROP": "test_token"})
    @patch.object(httpx, "get")
    def test_get_raindrop_by_raindrop_id(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"items": [{"_id": "1", "title": "Collection 1", "count": 10},
                                                             {"_id": "2", "title": "Collection 2", "count": 20}]}
        raindrop = Raindrop()
        mock_get.return_value.json.return_value = {"item": {"_id": "1", "title": "Raindrop 1", "excerpt": "excerpt 1",
                                                            "tags": ["tag1", "tag2"], "link": "https://example.com/1"}}
        raindrop_item = raindrop.getRaindropByRaindropId("1")
        assert raindrop_item == {"1": {"excerpt": "excerpt 1", "tags": ["tag1", "tag2"], "title": "Raindrop 1",
                                       "link": "https://example.com/1", "type": "raindrop"}}
        mock_get.assert_called_with("https://api.raindrop.io/rest/v1/raindrop/1", headers=raindrop._headers)
