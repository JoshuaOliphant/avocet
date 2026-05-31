# ABOUTME: Interaction tests for add/delete wired through modals to the fake API + DB.
# ABOUTME: Uses BaseFakeRaindrop to intercept API calls and asserts DB state after each flow.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.screens import AddBookmarkScreen, ConfirmDeleteScreen
from avocet.summary import StubSummaryProvider
from tests.fakes import BaseFakeRaindrop


class FakeAPI(BaseFakeRaindrop):
    def __init__(self):  # noqa: D401
        self.deleted: list[int] = []
        self.added: list[dict] = []

    async def get_collections(self):
        return [{"_id": 1, "title": "Reading"}]

    async def get_raindrops_by_collection_id(self, collection_id, search=None):
        return [{"_id": 10, "title": "Textual", "link": "https://x", "tags": []}]

    async def add_raindrop(self, link, collection_id, tags, title=""):
        item = {"_id": 99, "title": title or link, "link": link, "tags": tags}
        self.added.append({"link": link, "title": title, "tags": tags})
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


async def test_add_submits_and_persists():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        from textual.widgets import Button, Input

        assert isinstance(app.screen, AddBookmarkScreen)
        app.screen.query_one("#link", Input).value = "https://new.example"
        app.screen.query_one("#tags", Input).value = "py, tui"
        app.screen.query_one("#confirm", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        # API received the add with parsed tags
        assert len(api.added) == 1
        assert api.added[0]["link"] == "https://new.example"
        # row persisted to the DB (FakeAPI returns _id 99)
        assert app.db.get_raindrop(99) is not None


async def test_open_link_opens_browser(monkeypatch):
    opened = []
    import avocet.app as app_module

    monkeypatch.setattr(app_module.webbrowser, "open", lambda url: opened.append(url))
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import DataTable

        app.query_one("#bookmarks", DataTable).focus()
        await pilot.press("o")
        await pilot.pause()
        assert opened == ["https://x"]
