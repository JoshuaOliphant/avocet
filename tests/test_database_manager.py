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


def test_touch_and_get_last_update(db):
    assert db.get_last_update() is None
    db.touch_last_update()
    assert db.get_last_update() is not None
