# ABOUTME: Interaction tests for add/delete wired through modals to the fake API + DB.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.screens import AddBookmarkScreen, ConfirmDeleteScreen
from avocet.summary import StubSummaryProvider


class FakeAPI:
    def __init__(self):
        self.deleted: list[int] = []
        self.added: list[dict] = []

    async def get_collections(self):
        return [{"_id": 1, "title": "Reading"}]

    async def get_raindrops_by_collection_id(self, collection_id, search=None):
        return [{"_id": 10, "title": "Textual", "link": "https://x", "tags": []}]

    async def add_raindrop(self, link, collection_id, tags):
        item = {"_id": 99, "title": link, "link": link, "tags": tags}
        self.added.append(item)
        return item

    async def delete_raindrop(self, raindrop_id):
        self.deleted.append(raindrop_id)


def _seeded_db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    db.upsert_collection({"_id": 1, "title": "Reading"})
    db.upsert_raindrops(
        [{"_id": 10, "title": "Textual", "link": "https://x", "tags": []}], collection_id=1
    )
    return db


async def test_delete_removes_row_and_calls_api():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import DataTable

        table = app.query_one("#bookmarks", DataTable)
        table.focus()
        await pilot.press("d")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmDeleteScreen)
        await pilot.press("enter")  # activates the focused Delete button
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert 10 in api.deleted
        assert app.db.get_raindrop(10) is None


async def test_add_opens_modal():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, AddBookmarkScreen)
