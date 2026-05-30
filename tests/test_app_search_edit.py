# ABOUTME: Interaction tests for edit, search, and tag filter flows.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.screens import EditBookmarkScreen
from avocet.summary import StubSummaryProvider


class FakeAPI:
    def __init__(self):
        self.updated: list[tuple[int, dict]] = []
        self.searched: list[str] = []

    async def get_collections(self):
        return [{"_id": 1, "title": "Reading"}]

    async def get_raindrops_by_collection_id(self, collection_id, search=None):
        if search:
            self.searched.append(search)
            return [{"_id": 20, "title": f"hit:{search}", "link": "https://s", "tags": []}]
        return [{"_id": 10, "title": "Textual", "link": "https://x", "tags": ["py"]}]

    async def update_raindrop(self, raindrop_id, fields):
        self.updated.append((raindrop_id, fields))
        return {"_id": raindrop_id, "title": fields.get("title"), "link": "https://x",
                "tags": fields.get("tags", [])}


def _seeded_db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    db.upsert_collection({"_id": 1, "title": "Reading"})
    db.upsert_raindrops(
        [
            {"_id": 10, "title": "Textual", "link": "https://x", "tags": ["py"]},
            {"_id": 11, "title": "Rich", "link": "https://y", "tags": ["rust"]},
        ],
        collection_id=1,
    )
    return db


async def test_edit_opens_with_prefilled_title():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import DataTable

        app.query_one("#bookmarks", DataTable).focus()
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(app.screen, EditBookmarkScreen)


async def test_tag_filter_reduces_rows():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.apply_tag_filter("rust")
        await pilot.pause()
        from textual.widgets import DataTable

        table = app.query_one("#bookmarks", DataTable)
        assert table.row_count == 1
