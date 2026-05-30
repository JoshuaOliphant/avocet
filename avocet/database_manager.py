# ABOUTME: SQLAlchemy session wrapper over the local SQLite cache plus app settings.
# ABOUTME: Upserts collections/raindrops from raw Raindrop API dicts; the UI reads only from here.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from models import Base, Collection, Raindrop, Update

_RAINDROP_TS = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _RAINDROP_TS)
    except ValueError:
        return None


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str | None] = mapped_column(default=None)


class DatabaseManager:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.Session: sessionmaker[Session] = sessionmaker(bind=engine)

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def upsert_collection(self, data: dict) -> None:
        parent = data.get("parent") or {}
        with self.Session() as session:
            collection = session.get(Collection, data["_id"]) or Collection(id=data["_id"])
            collection.title = data.get("title")
            collection.description = data.get("description")
            collection.count = data.get("count")
            collection.parent_id = parent.get("$id")
            collection.created = _parse_ts(data.get("created"))
            collection.last_update = _parse_ts(data.get("lastUpdate"))
            session.merge(collection)
            session.commit()

    def upsert_raindrops(self, items: list[dict], collection_id: int) -> None:
        with self.Session() as session:
            for data in items:
                existing = session.get(Raindrop, data["_id"])
                cached_summary = existing.summary if existing else None
                raindrop = existing or Raindrop(id=data["_id"])
                raindrop.title = data.get("title")
                raindrop.excerpt = data.get("excerpt")
                raindrop.note = data.get("note")
                raindrop.link = data.get("link")
                raindrop.created = _parse_ts(data.get("created"))
                raindrop.last_update = _parse_ts(data.get("lastUpdate"))
                raindrop.collection_id = collection_id
                raindrop.tags = data.get("tags")
                raindrop.summary = cached_summary  # never clobber a cached summary
                session.merge(raindrop)
            session.commit()

    def get_collections(self) -> list[Collection]:
        with self.Session() as session:
            return list(session.scalars(select(Collection).order_by(Collection.title)))

    def get_raindrops_by_collection_id(self, collection_id: int) -> list[Raindrop]:
        with self.Session() as session:
            stmt = select(Raindrop).where(Raindrop.collection_id == collection_id)
            return list(session.scalars(stmt.order_by(Raindrop.created.desc())))

    def get_raindrop(self, raindrop_id: int) -> Raindrop | None:
        with self.Session() as session:
            return session.get(Raindrop, raindrop_id)

    def set_summary(self, raindrop_id: int, summary: str) -> None:
        with self.Session() as session:
            raindrop = session.get(Raindrop, raindrop_id)
            if raindrop is not None:
                raindrop.summary = summary
                session.commit()

    def remove_raindrop(self, raindrop_id: int) -> None:
        with self.Session() as session:
            raindrop = session.get(Raindrop, raindrop_id)
            if raindrop is not None:
                session.delete(raindrop)
                session.commit()

    def get_setting(self, key: str) -> str | None:
        with self.Session() as session:
            setting = session.get(Setting, key)
            return setting.value if setting else None

    def set_setting(self, key: str, value: str) -> None:
        with self.Session() as session:
            session.merge(Setting(key=key, value=value))
            session.commit()

    def touch_last_update(self) -> None:
        with self.Session() as session:
            update = session.get(Update, 1) or Update(id=1)
            update.last_update = datetime.now()
            session.merge(update)
            session.commit()

    def get_last_update(self) -> datetime | None:
        with self.Session() as session:
            update = session.get(Update, 1)
            return update.last_update if update else None
