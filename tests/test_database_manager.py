# ABOUTME: Tests for DatabaseManager against a real in-memory SQLite engine.
# ABOUTME: StaticPool keeps the schema alive across the sessions the manager opens.
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.database_manager import DatabaseManager


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    manager = DatabaseManager(engine=engine)
    manager.create_tables()
    return manager


def _collection(cid=1, title="Reading", parent_id=None):
    return {
        "_id": cid,
        "title": title,
        "description": "",
        "count": 2,
        "parent": {"$id": parent_id} if parent_id else None,
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdate": "2026-01-02T00:00:00.000Z",
    }


def _raindrop(rid=10, collection_id=1, title="Textual"):
    return {
        "_id": rid,
        "title": title,
        "excerpt": "An excerpt",
        "note": "A note",
        "link": "https://example.com",
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdate": "2026-01-02T00:00:00.000Z",
        "tags": ["py", "tui"],
    }


def test_upsert_and_get_collections(db):
    db.upsert_collection(_collection(1, "Reading"))
    db.upsert_collection(_collection(1, "Reading List"))  # same id -> update, not duplicate
    collections = db.get_collections()
    assert len(collections) == 1
    assert collections[0].title == "Reading List"


def test_upsert_raindrops_and_query_by_collection(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1), _raindrop(11, 1, "Rich")], collection_id=1)
    rows = db.get_raindrops_by_collection_id(1)
    assert {r.title for r in rows} == {"Textual", "Rich"}
    assert db.get_raindrop(10).tags == ["py", "tui"]


def test_set_summary_persists(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1)], collection_id=1)
    db.set_summary(10, "A concise summary.")
    assert db.get_raindrop(10).summary == "A concise summary."


def test_upsert_does_not_clobber_existing_summary(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1)], collection_id=1)
    db.set_summary(10, "Cached summary.")
    # Re-upsert the same raindrop (e.g. during a later sync) must NOT wipe the summary.
    db.upsert_raindrops([_raindrop(10, 1, "Textual Updated")], collection_id=1)
    refreshed = db.get_raindrop(10)
    assert refreshed.title == "Textual Updated"
    assert refreshed.summary == "Cached summary."


def test_remove_raindrop(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1)], collection_id=1)
    db.remove_raindrop(10)
    assert db.get_raindrop(10) is None


def test_set_and_get_setting(db):
    assert db.get_setting("missing") is None
    db.set_setting("theme", "catppuccin-mocha")
    assert db.get_setting("theme") == "catppuccin-mocha"


def test_get_all_raindrops_spans_collections(db):
    # The virtual "All" view reads every raindrop regardless of collection.
    db.upsert_collection(_collection(1, "Reading"))
    db.upsert_collection(_collection(2, "Work"))
    db.upsert_raindrops([_raindrop(10, 1)], collection_id=1)
    db.upsert_raindrops([_raindrop(20, 2)], collection_id=2)
    assert {r.id for r in db.get_all_raindrops()} == {10, 20}


def test_upsert_uses_item_real_collection_not_fallback(db):
    # A raindrop fetched via an aggregate view (fallback 0) must still be stored
    # under its true collection from the payload — never clobbered to 0.
    db.upsert_collection(_collection(7, "Real"))
    item = {"_id": 30, "title": "x", "tags": [], "collection": {"$id": 7}}
    db.upsert_raindrops([item], collection_id=0)
    assert db.get_raindrop(30).collection_id == 7
    assert db.get_raindrops_by_collection_id(0) == []


def test_upsert_falls_back_to_passed_collection_when_payload_omits_it(db):
    db.upsert_collection(_collection(1, "Reading"))
    db.upsert_raindrops([{"_id": 40, "title": "y", "tags": []}], collection_id=1)
    assert db.get_raindrop(40).collection_id == 1


def test_get_raindrops_by_ids_preserves_order_and_skips_missing(db):
    # Returns rows in the requested id order; ids with no row are skipped.
    db.upsert_collection(_collection(1, "Reading"))
    db.upsert_raindrops([_raindrop(10, 1), _raindrop(11, 1), _raindrop(12, 1)], collection_id=1)
    result = db.get_raindrops_by_ids([12, 999, 10])
    assert [r.id for r in result] == [12, 10]
