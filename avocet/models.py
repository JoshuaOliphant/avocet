# ABOUTME: SQLAlchemy 2.0 declarative models for collections, raindrops, and app settings.
# ABOUTME: Raindrop.summary is a nullable, lazily-populated Claude-generated summary.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(default=None)
    description: Mapped[str | None] = mapped_column(default=None)
    count: Mapped[int | None] = mapped_column(default=None)
    parent_id: Mapped[int | None] = mapped_column(default=None)
    created: Mapped[datetime | None] = mapped_column(default=None)
    last_update: Mapped[datetime | None] = mapped_column(default=None)

    raindrops: Mapped[list[Raindrop]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )


class Raindrop(Base):
    __tablename__ = "raindrops"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(default=None)
    excerpt: Mapped[str | None] = mapped_column(default=None)
    note: Mapped[str | None] = mapped_column(default=None)
    link: Mapped[str | None] = mapped_column(default=None)
    created: Mapped[datetime | None] = mapped_column(default=None)
    last_update: Mapped[datetime | None] = mapped_column(default=None)
    collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("collections.id"), default=None
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(default=None)

    collection: Mapped[Collection | None] = relationship(back_populates="raindrops")


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str | None] = mapped_column(default=None)
