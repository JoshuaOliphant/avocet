# ABOUTME: SQLAlchemy session wrapper over the local SQLite cache plus app settings.
# ABOUTME: Upserts collections/raindrops from raw Raindrop API dicts; the UI reads only from here.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from avocet.models import Base, Collection, Raindrop, Setting

_RAINDROP_TS = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _RAINDROP_TS)
    except ValueError:
        return None


def _item_collection_id(data: dict, fallback: int) -> int:
    # A raindrop's true collection comes from its own payload (`collection.$id`),
    # so a bookmark is always stored under its real collection even when fetched
    # via an aggregate view like the synthetic "All". Fall back to the caller's id
    # only when the payload omits it.
    collection = data.get("collection") or {}
    cid = collection.get("$id")
    if cid is None:
        cid = data.get("collectionId")
    return cid if cid is not None else fallback


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
                raindrop.collection_id = _item_collection_id(data, collection_id)
                raindrop.tags = data.get("tags") or []
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

    def get_all_raindrops(self) -> list[Raindrop]:
        with self.Session() as session:
            stmt = select(Raindrop).order_by(Raindrop.created.desc())
            return list(session.scalars(stmt))

    def get_raindrops_by_ids(self, ids: list[int]) -> list[Raindrop]:
        # Fetch many raindrops in a single query, returned in the given id order
        # (ids with no matching row are skipped).
        with self.Session() as session:
            found = {r.id: r for r in session.scalars(select(Raindrop).where(Raindrop.id.in_(ids)))}
        return [found[i] for i in ids if i in found]

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

