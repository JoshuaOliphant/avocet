# ABOUTME: Verifies theme changes persist to the DB settings table.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider


def _db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    return db


async def test_theme_change_persists():
    db = _db()
    app = Avocet(db=db, summary_provider=StubSummaryProvider())
    async with app.run_test() as pilot:
        app.theme = "nord"
        await pilot.pause()
    assert db.get_setting("theme") == "nord"
