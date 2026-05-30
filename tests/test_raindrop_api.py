# ABOUTME: Tests for the async Raindrop API client using pytest-httpx.
# ABOUTME: Proves pagination assembles all pages and nested+system collections are included.
import json as _json

import json

import httpx
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


async def test_add_raindrop_posts_expected_payload(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/raindrop", method="POST", json={"item": {"_id": 99, "link": "https://x"}}
    )
    result = await api.add_raindrop("https://x", 1, ["py"])
    assert result["_id"] == 99
    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    body = _json.loads(request.content)
    assert body == {"link": "https://x", "collectionId": 1, "pleaseParse": {}, "tags": ["py"]}


async def test_update_raindrop_puts_fields(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/raindrop/42", method="PUT", json={"item": {"_id": 42, "title": "New"}}
    )
    result = await api.update_raindrop(42, {"title": "New", "tags": ["a"]})
    assert result["title"] == "New"
    request = httpx_mock.get_requests()[0]
    assert request.method == "PUT"
    assert _json.loads(request.content) == {"title": "New", "tags": ["a"]}


async def test_delete_raindrop_issues_delete(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/raindrop/42", method="DELETE", json={"result": True})
    await api.delete_raindrop(42)
    assert httpx_mock.get_requests()[0].method == "DELETE"


async def test_get_raindrop_reads_item(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/raindrop/7", json={"item": {"_id": 7, "title": "Seven"}}
    )
    result = await api.get_raindrop(7)
    assert result["_id"] == 7


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
async def test_error_status_raises(api, httpx_mock: HTTPXMock):
    # A 401 must raise, not silently return an empty list (the bug this fixes).
    httpx_mock.add_response(url=f"{BASE}/collections", status_code=401, json={"error": "no"})
    with pytest.raises(httpx.HTTPStatusError):
        await api.get_collections()
