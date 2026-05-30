# ABOUTME: Verifies the app syncs from a (fake) RaindropAPI into the DB on refresh.
# ABOUTME: The fake API returns canned collections/raindrops; no network involved.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider
from tests.fakes import BaseFakeRaindrop


class FakeAPI(BaseFakeRaindrop):
    async def get_collections(self):
        return [{"_id": 0, "title": "All"}, {"_id": 1, "title": "Reading"}]

    async def get_raindrops_by_collection_id(self, collection_id, search=None):
        if collection_id == 1:
            return [{"_id": 10, "title": "Synced", "link": "https://x", "tags": []}]
        return []


def _empty_db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    return db


async def test_refresh_syncs_into_db():
    app = Avocet(db=_empty_db(), summary_provider=StubSummaryProvider(), api=FakeAPI())
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert any(c.title == "Reading" for c in app.db.get_collections())
