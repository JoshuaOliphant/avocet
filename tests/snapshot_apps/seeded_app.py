# ABOUTME: A deterministic Avocet instance for snapshot tests (seeded DB, stub summaries).
# ABOUTME: pytest-textual-snapshot runs this file as a standalone app for SVG capture.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider


def build_app() -> Avocet:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    db.upsert_collection({"_id": 0, "title": "All"})
    db.upsert_collection({"_id": 1, "title": "Python"})
    db.upsert_raindrops(
        [
            {
                "_id": 10,
                "title": "Textual docs",
                "link": "https://textual.textualize.io",
                "tags": ["py", "tui"],
                "created": "2026-05-01T00:00:00.000Z",
            },
            {
                "_id": 11,
                "title": "Raindrop API",
                "link": "https://developer.raindrop.io",
                "tags": ["api"],
                "created": "2026-04-15T00:00:00.000Z",
            },
        ],
        collection_id=1,
    )
    return Avocet(db=db, summary_provider=StubSummaryProvider())


app = build_app()

if __name__ == "__main__":
    app.run()
