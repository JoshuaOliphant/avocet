import pytest
from pytest_httpx import HTTPXMock
from avocet.raindrop_api import RaindropAPI

@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("RAINDROP", "fake_token_value")
    return RaindropAPI()

@pytest.mark.asyncio
async def test_get_collections(api: RaindropAPI, httpx_mock: HTTPXMock):
    # Mock the HTTP response
    httpx_mock.add_response(url="https://api.raindrop.io/rest/v1/collections", json={"items": [{"id": "1", "title": "Collection 1"}, {"id": "2", "title": "Collection 2"}]})

    # Call the method being tested
    collections = await api.get_collections()

    # Check the result
    assert len(collections) == 2
    assert collections[0]["id"] == "1"
    assert collections[0]["title"] == "Collection 1"
    assert collections[1]["id"] == "2"
    assert collections[1]["title"] == "Collection 2"

@pytest.mark.asyncio
async def test_get_raindrops_by_collection_id(api: RaindropAPI, httpx_mock: HTTPXMock):
    # Mock the HTTP response
    httpx_mock.add_response(url="https://api.raindrop.io/rest/v1/raindrops/1", json={"items": [{"id": "1", "title": "Raindrop 1"}, {"id": "2", "title": "Raindrop 2"}]})

    # Call the method being tested
    raindrops = await api.get_raindrops_by_collection_id("1")

    # Check the result
    assert len(raindrops) == 2
    assert raindrops[0]["id"] == "1"
    assert raindrops[0]["title"] == "Raindrop 1"
    assert raindrops[1]["id"] == "2"
    assert raindrops[1]["title"] == "Raindrop 2"

@pytest.mark.asyncio
async def test_get_raindrop_by_raindrop_id(api: RaindropAPI, httpx_mock: HTTPXMock):
    # Mock the HTTP response
    httpx_mock.add_response(url="https://api.raindrop.io/rest/v1/raindrop/1", 
                            json={"item":{"id": "1", "title": "Raindrop 1", "excerpt": "Excerpt 1", "link": "https://example.com/1", "tags": ["tag1", "tag2"]}})

    # Call the method being tested
    raindrop = await api.get_raindrop_by_raindrop_id("1")

    # Check the result
    assert raindrop["id"] == "1"
    assert raindrop["title"] == "Raindrop 1"