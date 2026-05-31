# ABOUTME: Interaction tests for edit, search, and tag filter flows.
# ABOUTME: Uses BaseFakeRaindrop to intercept edit/search calls and asserts DB and table state.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.screens import EditBookmarkScreen, TagFilterScreen
from avocet.summary import StubSummaryProvider
from tests.fakes import BaseFakeRaindrop


class FakeAPI(BaseFakeRaindrop):
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


async def test_edit_modal_prefills_current_title():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import DataTable, Input

        app.query_one("#bookmarks", DataTable).focus()
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(app.screen, EditBookmarkScreen)
        # The first row (id 10, "Textual") should be pre-filled in the title input.
        assert app.screen.query_one("#title", Input).value == "Textual"


async def test_edit_submits_and_updates_db():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Button, DataTable, Input

        app.query_one("#bookmarks", DataTable).focus()
        await pilot.press("e")
        await pilot.pause()
        title_input = app.screen.query_one("#title", Input)
        title_input.value = "Textual Updated"
        app.screen.query_one("#confirm", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert len(api.updated) == 1
        rid, fields = api.updated[0]
        assert rid == 10
        assert fields["title"] == "Textual Updated"
        updated_row = app.db.get_raindrop(10)
        assert updated_row is not None
        assert updated_row.title == "Textual Updated"


async def test_search_submits_and_repopulates():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Button, Input

        # ensure a collection is selected so _current_collection_id is set
        await pilot.press("slash")
        await pilot.pause()
        from avocet.screens import SearchScreen

        assert isinstance(app.screen, SearchScreen)
        app.screen.query_one("#query", Input).value = "rust"
        app.screen.query_one("#confirm", Button).press()
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert api.searched == ["rust"]
        # the search-returned bookmark (id 20) is now in the table/DB
        assert app.db.get_raindrop(20) is not None


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


async def test_tag_filter_clear_via_modal_restores_rows():
    api = FakeAPI()
    app = Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider(), api=api)
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Button, DataTable

        table = app.query_one("#bookmarks", DataTable)
        # filter to one tag first
        app.apply_tag_filter("rust")
        await pilot.pause()
        assert table.row_count == 1
        # now open the modal and press Clear -> dismisses with "" -> shows all rows
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, TagFilterScreen)
        app.screen.query_one("#clear", Button).press()
        await pilot.pause()
        assert table.row_count == 2
