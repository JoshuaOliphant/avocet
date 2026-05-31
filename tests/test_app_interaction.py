# ABOUTME: Interaction tests for the Avocet app via Textual's run_test/Pilot.
# ABOUTME: Uses a pre-seeded in-memory DB and the stub summary provider (no network).
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider


def _seeded_db() -> DatabaseManager:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    db.upsert_collection({"_id": 1, "title": "Reading", "count": 2})
    db.upsert_raindrops(
        [
            {"_id": 10, "title": "Textual", "link": "https://example.com/t", "tags": ["py"]},
            {"_id": 11, "title": "Rich", "link": "https://example.com/r", "tags": ["py"]},
        ],
        collection_id=1,
    )
    return db


def make_app() -> Avocet:
    return Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider())


@pytest.fixture
def app():
    return make_app()


async def test_collections_listed(app):
    async with app.run_test():
        from textual.widgets import ListView

        listview = app.query_one("#collections", ListView)
        assert listview.children  # at least one collection row


async def test_selecting_collection_populates_table(app):
    async with app.run_test() as pilot:
        from textual.widgets import DataTable

        await pilot.pause()
        table = app.query_one("#bookmarks", DataTable)
        assert table.row_count == 2


async def test_selecting_row_fills_summary(app):
    async with app.run_test() as pilot:
        from textual.widgets import DataTable

        await pilot.pause()
        table = app.query_one("#bookmarks", DataTable)
        table.focus()
        await pilot.press("enter")
        await pilot.pause()
        detail = app.query_one("#detail-summary")
        assert "Summary of" in str(detail.content)
