# ABOUTME: Tests for the async Raindrop API client using pytest-httpx.
# ABOUTME: Proves pagination assembles all pages and nested+system collections are included.
import pytest
from pytest_httpx import HTTPXMock

from avocet.raindrop_api import RaindropAPI

BASE = "https://api.raindrop.io/rest/v1"


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("RAINDROP", "fake-token")
    return RaindropAPI()


async def test_get_collections_merges_root_children_and_system(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/collections",
        json={"items": [{"_id": 1, "title": "Root"}]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/collections/childrens",
        json={"items": [{"_id": 2, "title": "Child", "parent": {"$id": 1}}]},
    )
    collections = await api.get_collections()
    ids = {c["_id"] for c in collections}
    assert {0, 1, 2} <= ids  # 0 is the synthetic "All" system collection


async def test_get_raindrops_paginates(api, httpx_mock: HTTPXMock):
    page0 = {"items": [{"_id": i} for i in range(50)]}
    page1 = {"items": [{"_id": i} for i in range(50, 73)]}  # < perpage -> last page
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=0", json=page0)
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=1", json=page1)
    items = await api.get_raindrops_by_collection_id(1)
    assert len(items) == 73


async def test_sends_bearer_token(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=0", json={"items": []})
    await api.get_raindrops_by_collection_id(1)
    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == "Bearer fake-token"
