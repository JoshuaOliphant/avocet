# Avocet Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize Avocet (a Textual TUI for Raindrop.io bookmarks) onto uv, Textual 8.x, SQLAlchemy 2.0, and a direct Claude summarizer, with a three-pane UI and a three-layer test suite including visual snapshot regression.

**Architecture:** A local SQLite database (via `DatabaseManager`) is the single source of truth for the UI. An async `RaindropAPI` httpx client syncs bookmarks into it (with correct pagination and nested/system collections). Summaries are produced lazily on bookmark selection by a `SummaryProvider` seam — `ClaudeSummaryProvider` in production, `StubSummaryProvider` in tests — and cached in SQLite. The `Avocet` Textual app renders a three-pane layout (collections `ListView`, bookmarks `DataTable`, detail panel) with CRUD modals, the Catppuccin Mocha theme, and a runtime theme switcher via the command palette.

**Tech Stack:** Python 3.12+, uv, Textual 8.2.x, SQLAlchemy 2.0, httpx, anthropic, platformdirs, pytest + pytest-asyncio + pytest-httpx + pytest-mock + pytest-textual-snapshot, ruff, ty.

**Source spec:** `docs/superpowers/specs/2026-05-29-avocet-modernization-design.md`

---

## Conventions for every task

- All files under `avocet/` use **bare imports** (`from raindrop_api import RaindropAPI`), matching the existing layout and the `pythonpath` in `pyproject.toml`. Tests use **package imports** (`from avocet.raindrop_api import RaindropAPI`).
- Every new `.py` file starts with two `ABOUTME:` comment lines.
- Run a single test with `uv run pytest <path>::<name> -v`.
- Commit after each task with a conventional-commit message.

---

## Phase 1 — Toolchain & dependency migration

Goal: project builds and runs on uv with a pruned dependency set, ruff, ty, and updated CI. The app still behaves as before at the end of this phase (old `app.py`/`ai.py` remain until Phase 2/3 replace them).

### Task 1.1: Convert pyproject.toml to PEP 621 + uv

**Files:**
- Modify: `pyproject.toml` (full rewrite)
- Delete: `poetry.lock`, `uv.lock` (stub)

- [ ] **Step 1: Replace `pyproject.toml` with PEP 621 + uv layout**

```toml
[project]
name = "avocet"
version = "0.2.0"
description = "A TUI for Raindrop.io bookmarks written in Python"
authors = [{ name = "Joshua Oliphant", email = "joshua.oliphant@hey.com" }]
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    "textual>=8.2,<9",
    "httpx>=0.28",
    "sqlalchemy>=2.0",
    "anthropic>=0.40",
    "platformdirs>=4.0",
]

[project.scripts]
avocet = "avocet.app:main"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-httpx>=0.35",
    "pytest-mock>=3.14",
    "pytest-textual-snapshot>=1.0",
    "textual-dev>=1.7",
    "ruff>=0.8",
    "ty>=0.0.1a1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["avocet"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = [".", "avocet", "tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.ty.environment]
python-version = "3.12"
```

- [ ] **Step 2: Delete old lockfiles**

```bash
rm -f poetry.lock uv.lock
```

- [ ] **Step 3: Generate the uv environment and lockfile**

Run: `uv sync`
Expected: creates `.venv` and a real `uv.lock`; exits 0. (If `ty`'s version specifier fails to resolve, relax it to `"ty"` with no version and re-run.)

- [ ] **Step 4: Verify the toolchain runs**

Run: `uv run python -c "import textual, sqlalchemy, anthropic, httpx, platformdirs; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git rm --cached poetry.lock 2>/dev/null || true
git commit -m "build: migrate from poetry to uv with pruned dependencies"
```

### Task 1.2: Rewrite justfile and CI for uv

**Files:**
- Modify: `justfile`
- Modify: `.github/workflows/python-app.yml`

- [ ] **Step 1: Replace `justfile`**

```just
set positional-arguments

alias r := run
alias t := test
alias i := install
alias l := lint

install:
	uv sync

run:
	uv run textual run --dev avocet/app.py

console:
	uv run textual console

test:
	uv run pytest

snapshot-update:
	uv run pytest --snapshot-update

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

commit message:
	git commit -am "$1"
```

- [ ] **Step 2: Replace `.github/workflows/python-app.yml`**

```yaml
name: Python application

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync --locked
      - name: Lint with ruff
        run: uv run ruff check .
      - name: Type check with ty
        run: uv run ty check
      - name: Test with pytest
        run: uv run pytest
```

- [ ] **Step 3: Verify lint runs**

Run: `uv run ruff check . || true`
Expected: ruff executes (may report findings in the legacy files; that is fine — they get replaced in Phase 2/3).

- [ ] **Step 4: Commit**

```bash
git add justfile .github/workflows/python-app.yml
git commit -m "build: run tasks and CI through uv on python 3.12 and 3.13"
```

### Task 1.3: Repo hygiene — remove committed DB, ignore caches

**Files:**
- Delete: `avocet.sqlite`
- Modify: `.gitignore`

- [ ] **Step 1: Remove the committed database**

```bash
git rm --cached avocet.sqlite
rm -f avocet.sqlite
```

- [ ] **Step 2: Append ignore rules to `.gitignore`**

Add these lines to `.gitignore`:

```gitignore
# Local SQLite cache
*.sqlite
*.sqlite3

# uv
.venv/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: stop tracking local sqlite cache and venv"
```

---

## Phase 2 — Data layer rewrite

Goal: a correct async Raindrop client (pagination + nested/system collections), SQLAlchemy 2.0 typed models and `DatabaseManager`, and the summary provider seam — all fully unit-tested. No UI changes yet.

### Task 2.1: SQLAlchemy 2.0 typed models

**Files:**
- Modify: `avocet/models.py` (full rewrite)
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for the SQLAlchemy declarative models.
# ABOUTME: Verifies table creation and the Raindrop.summary nullable column.
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from avocet.models import Base, Collection, Raindrop, Update


def test_tables_create():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    names = set(inspect(engine).get_table_names())
    assert {"collections", "raindrops", "update"} <= names


def test_raindrop_summary_is_nullable():
    summary_col = Raindrop.__table__.c.summary
    assert summary_col.nullable is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL (import error — new model API not present).

- [ ] **Step 3: Rewrite `avocet/models.py`**

```python
# ABOUTME: SQLAlchemy 2.0 declarative models for collections, raindrops, and sync state.
# ABOUTME: Raindrop.summary is a nullable, lazily-populated Claude-generated summary.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, JSON
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

    raindrops: Mapped[list["Raindrop"]] = relationship(
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
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    summary: Mapped[str | None] = mapped_column(default=None)

    collection: Mapped["Collection | None"] = relationship(back_populates="raindrops")


class Update(Base):
    __tablename__ = "update"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_update: Mapped[datetime | None] = mapped_column(default=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/models.py tests/test_models.py
git commit -m "feat: typed sqlalchemy 2.0 models with nullable summary and parent_id"
```

### Task 2.2: DatabaseManager over a real engine

**Files:**
- Modify: `avocet/database_manager.py` (full rewrite)
- Test: `tests/test_database_manager.py` (full rewrite)

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for DatabaseManager against a real in-memory SQLite engine.
# ABOUTME: StaticPool keeps the schema alive across the sessions the manager opens.
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.database_manager import DatabaseManager


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    manager = DatabaseManager(engine=engine)
    manager.create_tables()
    return manager


def _collection(cid=1, title="Reading", parent_id=None):
    return {
        "_id": cid,
        "title": title,
        "description": "",
        "count": 2,
        "parent": {"$id": parent_id} if parent_id else None,
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdate": "2026-01-02T00:00:00.000Z",
    }


def _raindrop(rid=10, collection_id=1, title="Textual"):
    return {
        "_id": rid,
        "title": title,
        "excerpt": "An excerpt",
        "note": "A note",
        "link": "https://example.com",
        "created": "2026-01-01T00:00:00.000Z",
        "lastUpdate": "2026-01-02T00:00:00.000Z",
        "tags": ["py", "tui"],
    }


def test_upsert_and_get_collections(db):
    db.upsert_collection(_collection(1, "Reading"))
    db.upsert_collection(_collection(1, "Reading List"))  # same id -> update, not duplicate
    collections = db.get_collections()
    assert len(collections) == 1
    assert collections[0].title == "Reading List"


def test_upsert_raindrops_and_query_by_collection(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1), _raindrop(11, 1, "Rich")], collection_id=1)
    rows = db.get_raindrops_by_collection_id(1)
    assert {r.title for r in rows} == {"Textual", "Rich"}
    assert db.get_raindrop(10).tags == ["py", "tui"]


def test_set_summary_persists(db):
    db.upsert_collection(_collection(1))
    db.upsert_raindrops([_raindrop(10, 1)], collection_id=1)
    db.set_summary(10, "A concise summary.")
    assert db.get_raindrop(10).summary == "A concise summary."


def test_set_and_get_setting(db):
    assert db.get_setting("missing") is None
    db.set_setting("theme", "catppuccin-mocha")
    assert db.get_setting("theme") == "catppuccin-mocha"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_database_manager.py -v`
Expected: FAIL (new method names not present).

- [ ] **Step 3: Rewrite `avocet/database_manager.py`**

```python
# ABOUTME: SQLAlchemy session wrapper over the local SQLite cache plus app settings.
# ABOUTME: Upserts collections/raindrops from raw Raindrop API dicts; the UI reads only from here.
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Collection, Raindrop, Update

_RAINDROP_TS = "%Y-%m-%dT%H:%M:%S.%fZ"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _RAINDROP_TS)
    except ValueError:
        return None


class _Setting(Base):
    __tablename__ = "settings"
    from sqlalchemy.orm import Mapped, mapped_column

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
                raindrop = session.get(Raindrop, data["_id"]) or Raindrop(id=data["_id"])
                existing_summary = raindrop.summary
                raindrop.title = data.get("title")
                raindrop.excerpt = data.get("excerpt")
                raindrop.note = data.get("note")
                raindrop.link = data.get("link")
                raindrop.created = _parse_ts(data.get("created"))
                raindrop.last_update = _parse_ts(data.get("lastUpdate"))
                raindrop.collection_id = collection_id
                raindrop.tags = data.get("tags")
                raindrop.summary = existing_summary  # never clobber a cached summary
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
            setting = session.get(_Setting, key)
            return setting.value if setting else None

    def set_setting(self, key: str, value: str) -> None:
        with self.Session() as session:
            session.merge(_Setting(key=key, value=value))
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_database_manager.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/database_manager.py tests/test_database_manager.py
git commit -m "feat: rewrite DatabaseManager with upserts, summary cache, and settings"
```

### Task 2.3: Async RaindropAPI with pagination and nested/system collections

**Files:**
- Modify: `avocet/raindrop_api.py` (full rewrite)
- Test: `tests/test_raindrop_api.py` (full rewrite)

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for the async Raindrop API client using pytest-httpx.
# ABOUTME: Proves pagination assembles all pages and nested+system collections are included.
import pytest
from pytest_httpx import HTTPXMock

from avocet.raindrop_api import RaindropAPI

BASE = "https://api.raindrop.io/rest/v1"


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("RAINDROP", "fake-token")
    return RaindropAPI()


async def test_get_collections_merges_root_children_and_system(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/collections",
        json={"items": [{"_id": 1, "title": "Root"}]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/collections/childrens",
        json={"items": [{"_id": 2, "title": "Child", "parent": {"$id": 1}}]},
    )
    collections = await api.get_collections()
    ids = {c["_id"] for c in collections}
    assert {0, 1, 2} <= ids  # 0 is the synthetic "All" system collection


async def test_get_raindrops_paginates(api, httpx_mock: HTTPXMock):
    page0 = {"items": [{"_id": i} for i in range(50)]}
    page1 = {"items": [{"_id": i} for i in range(50, 73)]}  # < perpage -> last page
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=0", json=page0)
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=1", json=page1)
    items = await api.get_raindrops_by_collection_id(1)
    assert len(items) == 73


async def test_sends_bearer_token(api, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/raindrops/1?perpage=50&page=0", json={"items": []})
    await api.get_raindrops_by_collection_id(1)
    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == "Bearer fake-token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_raindrop_api.py -v`
Expected: FAIL (new method behavior not present).

- [ ] **Step 3: Rewrite `avocet/raindrop_api.py`**

```python
# ABOUTME: Async httpx client for the Raindrop.io REST API.
# ABOUTME: Paginates raindrops and merges root, nested, and the synthetic "All" collection.
from __future__ import annotations

import os

import httpx

BASE_URL = "https://api.raindrop.io/rest/v1"
PER_PAGE = 50
SYSTEM_ALL = {"_id": 0, "title": "All", "parent": None}


class RaindropAPI:
    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ["RAINDROP"]
        self._headers = {"Authorization": f"Bearer {self._token}"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers, base_url=BASE_URL, timeout=30.0)

    async def get_collections(self) -> list[dict]:
        async with self._client() as client:
            root = (await client.get("/collections")).json().get("items", [])
            children = (await client.get("/collections/childrens")).json().get("items", [])
        return [SYSTEM_ALL, *root, *children]

    async def get_raindrops_by_collection_id(
        self, collection_id: int, search: str | None = None
    ) -> list[dict]:
        items: list[dict] = []
        page = 0
        async with self._client() as client:
            while True:
                params: dict[str, object] = {"perpage": PER_PAGE, "page": page}
                if search:
                    params["search"] = search
                batch = (
                    await client.get(f"/raindrops/{collection_id}", params=params)
                ).json().get("items", [])
                items.extend(batch)
                if len(batch) < PER_PAGE:
                    break
                page += 1
        return items

    async def get_raindrop(self, raindrop_id: int) -> dict:
        async with self._client() as client:
            return (await client.get(f"/raindrop/{raindrop_id}")).json().get("item", {})

    async def add_raindrop(self, link: str, collection_id: int, tags: list[str]) -> dict:
        payload = {"link": link, "collectionId": collection_id, "pleaseParse": {}, "tags": tags}
        async with self._client() as client:
            return (await client.post("/raindrop", json=payload)).json().get("item", {})

    async def update_raindrop(self, raindrop_id: int, fields: dict) -> dict:
        async with self._client() as client:
            return (
                await client.put(f"/raindrop/{raindrop_id}", json=fields)
            ).json().get("item", {})

    async def delete_raindrop(self, raindrop_id: int) -> None:
        async with self._client() as client:
            await client.delete(f"/raindrop/{raindrop_id}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_raindrop_api.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/raindrop_api.py tests/test_raindrop_api.py
git commit -m "feat: async raindrop client with pagination and nested/system collections"
```

### Task 2.4: Summary provider seam (Claude + stub)

**Files:**
- Create: `avocet/summary.py`
- Delete: `avocet/ai.py`
- Test: `tests/test_summary.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for the summary provider seam.
# ABOUTME: StubSummaryProvider is deterministic and never touches the network.
from avocet.models import Raindrop
from avocet.summary import StubSummaryProvider


async def test_stub_provider_is_deterministic():
    provider = StubSummaryProvider()
    raindrop = Raindrop(id=1, title="Textual", link="https://example.com")
    first = await provider.summarize(raindrop)
    second = await provider.summarize(raindrop)
    assert first == second
    assert "Textual" in first
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_summary.py -v`
Expected: FAIL (module does not exist).

- [ ] **Step 3: Create `avocet/summary.py` and delete `ai.py`**

```python
# ABOUTME: Summary provider seam — ClaudeSummaryProvider (real) and StubSummaryProvider (tests).
# ABOUTME: Fetches a bookmark's page text and asks Claude for a concise summary, cached by the DB.
from __future__ import annotations

import os
from typing import Protocol

import httpx

from models import Raindrop

CLAUDE_MODEL = "claude-haiku-4-5"
_SYSTEM_PROMPT = (
    "You are a concise bookmarking assistant. Given the text of a web page, write a "
    "2-3 sentence summary capturing what the page is about and why someone saved it. "
    "Do not include preamble; output only the summary."
)


class SummaryProvider(Protocol):
    async def summarize(self, raindrop: Raindrop) -> str: ...


class StubSummaryProvider:
    """Deterministic, network-free provider for tests and snapshots."""

    async def summarize(self, raindrop: Raindrop) -> str:
        title = raindrop.title or "this bookmark"
        return f"Summary of {title}. A deterministic placeholder used in tests."


class ClaudeSummaryProvider:
    """Fetches page text and asks Claude (Haiku) for a concise summary."""

    def __init__(self, api_key: str | None = None) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    async def _fetch_page_text(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url)
            return response.text[:20000]

    async def summarize(self, raindrop: Raindrop) -> str:
        page_text = ""
        if raindrop.link:
            try:
                page_text = await self._fetch_page_text(raindrop.link)
            except httpx.HTTPError:
                page_text = ""
        content = page_text or (raindrop.excerpt or raindrop.title or "")
        message = await self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Title: {raindrop.title}\n\nPage text:\n{content}",
                }
            ],
        )
        return "".join(block.text for block in message.content if block.type == "text").strip()
```

```bash
git rm avocet/ai.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_summary.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Run the whole Phase 2 suite**

Run: `uv run pytest -v`
Expected: all tests pass (models, database_manager, raindrop_api, summary).

- [ ] **Step 6: Commit**

```bash
git add avocet/summary.py tests/test_summary.py
git commit -m "feat: claude summary provider with stub seam; remove langchain ai module"
```

---

## Phase 3 — New three-pane UI + theme

Goal: replace `app.py` with a Textual 8.x three-pane app (collections / bookmarks table / detail), Catppuccin Mocha theme, runtime theme switching, and lazy summaries on selection — driven by an injected `SummaryProvider` and `DatabaseManager`. Interaction-tested with `run_test`/`Pilot`.

### Task 3.1: App skeleton with dependency injection and DB-backed panes

**Files:**
- Modify: `avocet/app.py` (full rewrite)
- Create: `avocet/avocet.tcss` (overwrite the existing one)
- Test: `tests/test_app_interaction.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Interaction tests for the Avocet app via Textual's run_test/Pilot.
# ABOUTME: Uses a pre-seeded in-memory DB and the stub summary provider (no network).
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider


def _seeded_db() -> DatabaseManager:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db = DatabaseManager(engine=engine)
    db.create_tables()
    db.upsert_collection({"_id": 1, "title": "Reading", "count": 2})
    db.upsert_raindrops(
        [
            {"_id": 10, "title": "Textual", "link": "https://example.com/t", "tags": ["py"]},
            {"_id": 11, "title": "Rich", "link": "https://example.com/r", "tags": ["py"]},
        ],
        collection_id=1,
    )
    return db


def make_app() -> Avocet:
    return Avocet(db=_seeded_db(), summary_provider=StubSummaryProvider())


@pytest.fixture
def app():
    return make_app()


async def test_collections_listed(app):
    async with app.run_test() as pilot:
        from textual.widgets import ListView

        listview = app.query_one("#collections", ListView)
        assert listview.children  # at least one collection row


async def test_selecting_collection_populates_table(app):
    async with app.run_test() as pilot:
        from textual.widgets import DataTable

        await pilot.pause()
        table = app.query_one("#bookmarks", DataTable)
        assert table.row_count == 2


async def test_selecting_row_fills_summary(app):
    async with app.run_test() as pilot:
        from textual.widgets import DataTable

        await pilot.pause()
        table = app.query_one("#bookmarks", DataTable)
        table.focus()
        await pilot.press("enter")
        await pilot.pause()
        detail = app.query_one("#detail-summary")
        assert "Summary of" in str(detail.renderable)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_interaction.py -v`
Expected: FAIL (new `Avocet(db=..., summary_provider=...)` constructor not present).

- [ ] **Step 3: Rewrite `avocet/app.py`**

```python
# ABOUTME: Avocet — a Textual TUI for browsing Raindrop.io bookmarks (three-pane layout).
# ABOUTME: The local DB is the source of truth; summaries are generated lazily on row selection.
from __future__ import annotations

import os
import webbrowser

from sqlalchemy import create_engine
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Label, Static

from database_manager import DatabaseManager
from models import Raindrop
from raindrop_api import RaindropAPI
from summary import ClaudeSummaryProvider, SummaryProvider

CATPPUCCIN_MOCHA = Theme(
    name="catppuccin-mocha",
    primary="#89b4fa",
    secondary="#cba6f7",
    accent="#f5c2e7",
    foreground="#cdd6f4",
    background="#1e1e2e",
    surface="#313244",
    panel="#45475a",
    success="#a6e3a1",
    warning="#f9e2af",
    error="#f38ba8",
    dark=True,
)


def _default_db() -> DatabaseManager:
    from platformdirs import user_cache_dir
    from pathlib import Path

    cache_dir = Path(user_cache_dir("avocet"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{cache_dir / 'avocet.sqlite'}")
    manager = DatabaseManager(engine=engine)
    manager.create_tables()
    return manager


class Avocet(App):
    CSS_PATH = "avocet.tcss"
    BINDINGS = [
        ("o", "open_link", "Open in browser"),
        ("r", "refresh", "Refresh"),
        ("/", "search", "Search"),
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("f", "filter_tag", "Filter tag"),
    ]

    def __init__(
        self,
        db: DatabaseManager | None = None,
        summary_provider: SummaryProvider | None = None,
        api: RaindropAPI | None = None,
    ) -> None:
        super().__init__()
        self.db = db or _default_db()
        self.summary_provider = summary_provider or ClaudeSummaryProvider()
        self.api = api
        self._row_to_raindrop: dict[str, int] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ListView(id="collections")
            with Vertical(id="main"):
                yield DataTable(id="bookmarks", cursor_type="row")
                with Vertical(id="detail"):
                    yield Label("", id="detail-title")
                    yield Static("", id="detail-meta")
                    yield Static("", id="detail-summary")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(CATPPUCCIN_MOCHA)
        self.theme = self.db.get_setting("theme") or "catppuccin-mocha"
        table = self.query_one("#bookmarks", DataTable)
        table.add_column("Title", key="title")
        table.add_column("Tags", key="tags")
        table.add_column("Created", key="created")
        self._load_collections()

    def _load_collections(self) -> None:
        listview = self.query_one("#collections", ListView)
        listview.clear()
        collections = self.db.get_collections()
        for collection in collections:
            item = ListItem(Label(collection.title or "(untitled)"))
            item.collection_id = collection.id  # type: ignore[attr-defined]
            listview.append(item)
        if collections:
            self._populate_table(collections[0].id)

    def _populate_table(self, collection_id: int) -> None:
        table = self.query_one("#bookmarks", DataTable)
        table.clear()
        self._row_to_raindrop.clear()
        for raindrop in self.db.get_raindrops_by_collection_id(collection_id):
            row_key = str(raindrop.id)
            created = raindrop.created.strftime("%Y-%m-%d") if raindrop.created else ""
            tags = " ".join(f"#{t}" for t in (raindrop.tags or []))
            table.add_row(raindrop.title or "", tags, created, key=row_key)
            self._row_to_raindrop[row_key] = raindrop.id

    @on(ListView.Selected, "#collections")
    def _collection_selected(self, event: ListView.Selected) -> None:
        collection_id = getattr(event.item, "collection_id", None)
        if collection_id is not None:
            self._populate_table(collection_id)

    @on(DataTable.RowSelected, "#bookmarks")
    def _row_selected(self, event: DataTable.RowSelected) -> None:
        raindrop_id = self._row_to_raindrop.get(str(event.row_key.value))
        if raindrop_id is not None:
            self._show_detail(raindrop_id)

    def _show_detail(self, raindrop_id: int) -> None:
        raindrop = self.db.get_raindrop(raindrop_id)
        if raindrop is None:
            return
        self.query_one("#detail-title", Label).update(raindrop.title or "")
        tags = " ".join(f"#{t}" for t in (raindrop.tags or []))
        self.query_one("#detail-meta", Static).update(f"{tags}  ·  {raindrop.link or ''}")
        if raindrop.summary:
            self.query_one("#detail-summary", Static).update(raindrop.summary)
        else:
            self.query_one("#detail-summary", Static).update("Generating summary…")
            self._generate_summary(raindrop_id)

    @work(exclusive=True)
    async def _generate_summary(self, raindrop_id: int) -> None:
        raindrop = self.db.get_raindrop(raindrop_id)
        if raindrop is None:
            return
        summary = await self.summary_provider.summarize(raindrop)
        self.db.set_summary(raindrop_id, summary)
        # Only update the panel if this row is still the selected one.
        table = self.query_one("#bookmarks", DataTable)
        if table.cursor_row is not None:
            current_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            if str(current_key.value) == str(raindrop_id):
                self.query_one("#detail-summary", Static).update(summary)

    def _selected_raindrop(self) -> Raindrop | None:
        table = self.query_one("#bookmarks", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return None
        key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        raindrop_id = self._row_to_raindrop.get(str(key.value))
        return self.db.get_raindrop(raindrop_id) if raindrop_id is not None else None

    def action_open_link(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop and raindrop.link:
            webbrowser.open(raindrop.link)

    def action_refresh(self) -> None:
        self.notify("Refresh wired up in Phase 4")

    def action_search(self) -> None:
        self.notify("Search wired up in Phase 4")

    def action_add(self) -> None:
        self.notify("Add wired up in Phase 4")

    def action_edit(self) -> None:
        self.notify("Edit wired up in Phase 4")

    def action_delete(self) -> None:
        self.notify("Delete wired up in Phase 4")

    def action_filter_tag(self) -> None:
        self.notify("Tag filter wired up in Phase 4")


def main() -> None:
    if "RAINDROP" not in os.environ:
        raise SystemExit("Set the RAINDROP environment variable to your Raindrop.io API token.")
    Avocet().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `avocet/avocet.tcss`**

```css
/* ABOUTME: Styling for the Avocet three-pane layout. */
/* ABOUTME: Collections sidebar, bookmarks table, and detail panel. */
#collections {
    width: 28;
    border-right: solid $panel;
}

#main {
    width: 1fr;
}

#bookmarks {
    height: 2fr;
}

#detail {
    height: 1fr;
    border-top: solid $panel;
    padding: 0 1;
}

#detail-title {
    text-style: bold;
    color: $accent;
}

#detail-meta {
    color: $secondary;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_app_interaction.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add avocet/app.py avocet/avocet.tcss tests/test_app_interaction.py
git commit -m "feat: three-pane Avocet app with catppuccin theme and lazy summaries"
```

### Task 3.2: Sync-on-demand worker and refresh

**Files:**
- Modify: `avocet/app.py` (replace the `action_refresh` body and add a sync worker)
- Test: `tests/test_app_sync.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Verifies the app syncs from a (fake) RaindropAPI into the DB on refresh.
# ABOUTME: The fake API returns canned collections/raindrops; no network involved.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.summary import StubSummaryProvider


class FakeAPI:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_sync.py -v`
Expected: FAIL (`action_refresh` only notifies; nothing synced).

- [ ] **Step 3: Replace the `action_refresh` method and add a worker in `avocet/app.py`**

Replace the existing `action_refresh` method body with:

```python
    def action_refresh(self) -> None:
        if self.api is None:
            self.api = RaindropAPI()
        self._sync()

    @work(exclusive=True, group="sync")
    async def _sync(self) -> None:
        assert self.api is not None
        collections = await self.api.get_collections()
        for collection in collections:
            self.db.upsert_collection(collection)
            items = await self.api.get_raindrops_by_collection_id(collection["_id"])
            self.db.upsert_raindrops(items, collection["_id"])
        self.db.touch_last_update()
        self._load_collections()
        self.notify("Synced from Raindrop.io")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app_sync.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/app.py tests/test_app_sync.py
git commit -m "feat: sync bookmarks from raindrop into the local db on refresh"
```

### Task 3.3: Theme switching persists

**Files:**
- Modify: `avocet/app.py` (add a `watch_theme` to persist the choice)
- Test: `tests/test_app_theme.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_theme.py -v`
Expected: FAIL (theme not persisted).

- [ ] **Step 3: Add `watch_theme` to `Avocet` in `avocet/app.py`**

Add this method to the `Avocet` class:

```python
    def watch_theme(self, theme_name: str) -> None:
        # Persist the selected theme so it is restored on next launch.
        if getattr(self, "db", None) is not None:
            self.db.set_setting("theme", theme_name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app_theme.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/app.py tests/test_app_theme.py
git commit -m "feat: persist theme selection across launches"
```

---

## Phase 4 — CRUD features (search, tag filter, add, edit, delete)

Goal: replace the Phase 3 `notify` placeholders with real modal screens and API wiring. Each feature is its own `ModalScreen`, interaction-tested with the fake API + stub provider.

### Task 4.1: Modal screens module

**Files:**
- Create: `avocet/screens.py`
- Test: `tests/test_screens.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for the modal screen dataclasses/result payloads.
# ABOUTME: Confirms AddResult carries the fields the app needs to call the API.
from avocet.screens import AddResult


def test_add_result_fields():
    result = AddResult(link="https://x", collection_id=1, tags=["py", "tui"])
    assert result.link == "https://x"
    assert result.collection_id == 1
    assert result.tags == ["py", "tui"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_screens.py -v`
Expected: FAIL (module does not exist).

- [ ] **Step 3: Create `avocet/screens.py`**

```python
# ABOUTME: Modal screens for Avocet: add, edit, delete-confirm, search, and tag filter.
# ABOUTME: Each screen dismisses with a typed result the app uses to call the Raindrop API.
from __future__ import annotations

from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


@dataclass
class AddResult:
    link: str
    collection_id: int
    tags: list[str] = field(default_factory=list)


@dataclass
class EditResult:
    raindrop_id: int
    title: str
    tags: list[str] = field(default_factory=list)


def _parse_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


class AddBookmarkScreen(ModalScreen[AddResult | None]):
    def __init__(self, collection_id: int) -> None:
        super().__init__()
        self._collection_id = collection_id

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Add bookmark")
            yield Input(placeholder="https://…", id="link")
            yield Input(placeholder="tags, comma, separated", id="tags")
            yield Button("Add", id="confirm", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            link = self.query_one("#link", Input).value.strip()
            tags = _parse_tags(self.query_one("#tags", Input).value)
            if link:
                self.dismiss(AddResult(link=link, collection_id=self._collection_id, tags=tags))
                return
        self.dismiss(None)


class EditBookmarkScreen(ModalScreen[EditResult | None]):
    def __init__(self, raindrop_id: int, title: str, tags: list[str]) -> None:
        super().__init__()
        self._raindrop_id = raindrop_id
        self._title = title
        self._tags = tags

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Edit bookmark")
            yield Input(value=self._title, id="title")
            yield Input(value=", ".join(self._tags), id="tags")
            yield Button("Save", id="confirm", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            title = self.query_one("#title", Input).value.strip()
            tags = _parse_tags(self.query_one("#tags", Input).value)
            self.dismiss(EditResult(raindrop_id=self._raindrop_id, title=title, tags=tags))
            return
        self.dismiss(None)


class ConfirmDeleteScreen(ModalScreen[bool]):
    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Delete “{self._title}”?")
            yield Button("Delete", id="confirm", variant="error")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class SearchScreen(ModalScreen[str | None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Search Raindrop")
            yield Input(placeholder="search query…", id="query")
            yield Button("Search", id="confirm", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            query = self.query_one("#query", Input).value.strip()
            self.dismiss(query or None)
            return
        self.dismiss(None)


class TagFilterScreen(ModalScreen[str | None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Filter by tag")
            yield Input(placeholder="tag", id="tag")
            yield Button("Filter", id="confirm", variant="primary")
            yield Button("Clear", id="clear")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(self.query_one("#tag", Input).value.strip() or None)
        elif event.button.id == "clear":
            self.dismiss("")
        else:
            self.dismiss(None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_screens.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/screens.py tests/test_screens.py
git commit -m "feat: modal screens for add, edit, delete, search, and tag filter"
```

### Task 4.2: Wire add and delete into the app

**Files:**
- Modify: `avocet/app.py` (imports, `action_add`, `action_delete`, current-collection tracking)
- Test: `tests/test_app_crud.py`

- [ ] **Step 1: Write the failing test**

```python
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
        await pilot.press("enter")  # focuses/activates the first (Delete) button
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_crud.py -v`
Expected: FAIL (`action_add`/`action_delete` still call `notify`).

- [ ] **Step 3: Update `avocet/app.py`**

Add to the imports near the other local imports:

```python
from screens import (
    AddBookmarkScreen,
    AddResult,
    ConfirmDeleteScreen,
    EditBookmarkScreen,
    EditResult,
    SearchScreen,
    TagFilterScreen,
)
```

Track the current collection. In `_populate_table`, set it as the first line:

```python
    def _populate_table(self, collection_id: int) -> None:
        self._current_collection_id = collection_id
        table = self.query_one("#bookmarks", DataTable)
        # … rest unchanged …
```

And initialize it in `__init__` after `self._row_to_raindrop = {}`:

```python
        self._current_collection_id: int | None = None
```

Replace the `action_add` and `action_delete` methods:

```python
    def action_add(self) -> None:
        if self._current_collection_id is None:
            return

        def on_close(result: AddResult | None) -> None:
            if result is not None:
                self._do_add(result)

        self.push_screen(AddBookmarkScreen(self._current_collection_id), on_close)

    @work(exclusive=True, group="crud")
    async def _do_add(self, result: AddResult) -> None:
        if self.api is None:
            self.api = RaindropAPI()
        item = await self.api.add_raindrop(result.link, result.collection_id, result.tags)
        self.db.upsert_raindrops([item], result.collection_id)
        self._populate_table(result.collection_id)
        self.notify("Bookmark added")

    def action_delete(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop is None:
            return

        def on_close(confirmed: bool) -> None:
            if confirmed:
                self._do_delete(raindrop.id)

        self.push_screen(ConfirmDeleteScreen(raindrop.title or ""), on_close)

    @work(exclusive=True, group="crud")
    async def _do_delete(self, raindrop_id: int) -> None:
        if self.api is None:
            self.api = RaindropAPI()
        await self.api.delete_raindrop(raindrop_id)
        self.db.remove_raindrop(raindrop_id)
        if self._current_collection_id is not None:
            self._populate_table(self._current_collection_id)
        self.notify("Bookmark deleted")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app_crud.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add avocet/app.py tests/test_app_crud.py
git commit -m "feat: wire add and delete bookmark flows through modals"
```

### Task 4.3: Wire edit, search, and tag filter

**Files:**
- Modify: `avocet/app.py` (`action_edit`, `action_search`, `action_filter_tag`, a filtered populate path)
- Test: `tests/test_app_search_edit.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Interaction tests for edit, search, and tag filter flows.
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from avocet.app import Avocet
from avocet.database_manager import DatabaseManager
from avocet.screens import EditBookmarkScreen, SearchScreen, TagFilterScreen
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_search_edit.py -v`
Expected: FAIL (`apply_tag_filter` and real edit/search actions not present).

- [ ] **Step 3: Update `avocet/app.py`**

Replace `action_edit`, `action_search`, `action_filter_tag` and add helpers:

```python
    def action_edit(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop is None:
            return

        def on_close(result: EditResult | None) -> None:
            if result is not None:
                self._do_edit(result)

        self.push_screen(
            EditBookmarkScreen(raindrop.id, raindrop.title or "", raindrop.tags or []), on_close
        )

    @work(exclusive=True, group="crud")
    async def _do_edit(self, result: EditResult) -> None:
        if self.api is None:
            self.api = RaindropAPI()
        item = await self.api.update_raindrop(
            result.raindrop_id, {"title": result.title, "tags": result.tags}
        )
        if self._current_collection_id is not None:
            self.db.upsert_raindrops([item], self._current_collection_id)
            self._populate_table(self._current_collection_id)
        self.notify("Bookmark updated")

    def action_search(self) -> None:
        def on_close(query: str | None) -> None:
            if query and self._current_collection_id is not None:
                self._do_search(self._current_collection_id, query)

        self.push_screen(SearchScreen())

    @work(exclusive=True, group="search")
    async def _do_search(self, collection_id: int, query: str) -> None:
        if self.api is None:
            self.api = RaindropAPI()
        items = await self.api.get_raindrops_by_collection_id(collection_id, search=query)
        self.db.upsert_raindrops(items, collection_id)
        self._populate_table(collection_id)

    def action_filter_tag(self) -> None:
        def on_close(tag: str | None) -> None:
            if tag is not None:
                self.apply_tag_filter(tag)

        self.push_screen(TagFilterScreen(), on_close)

    def apply_tag_filter(self, tag: str) -> None:
        if self._current_collection_id is None:
            return
        table = self.query_one("#bookmarks", DataTable)
        table.clear()
        self._row_to_raindrop.clear()
        rows = self.db.get_raindrops_by_collection_id(self._current_collection_id)
        if tag:
            rows = [r for r in rows if tag in (r.tags or [])]
        for raindrop in rows:
            row_key = str(raindrop.id)
            created = raindrop.created.strftime("%Y-%m-%d") if raindrop.created else ""
            tags = " ".join(f"#{t}" for t in (raindrop.tags or []))
            table.add_row(raindrop.title or "", tags, created, key=row_key)
            self._row_to_raindrop[row_key] = raindrop.id
```

Note: the `action_search` `on_close` callback is passed via `push_screen(SearchScreen(), on_close)` — update that call to include the callback:

```python
        self.push_screen(SearchScreen(), on_close)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app_search_edit.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -v`
Expected: all unit + interaction tests pass.

- [ ] **Step 6: Commit**

```bash
git add avocet/app.py tests/test_app_search_edit.py
git commit -m "feat: wire edit, search, and tag filter flows"
```

---

## Phase 5 — Visual regression snapshots

Goal: SVG snapshot tests for the main view and each modal, made deterministic by a small launcher script that builds the app with a seeded in-memory DB + stub provider.

### Task 5.1: Deterministic snapshot launcher

**Files:**
- Create: `tests/snapshot_apps/seeded_app.py`

- [ ] **Step 1: Create the launcher**

```python
# ABOUTME: A deterministic Avocet instance for snapshot tests (seeded DB, stub summaries).
# ABOUTME: pytest-textual-snapshot runs this file as a standalone app for SVG capture.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
```

- [ ] **Step 2: Verify it launches headlessly**

Run: `uv run python -c "import asyncio; from tests.snapshot_apps.seeded_app import build_app; asyncio.run(build_app().run_test().__aenter__())"`
Expected: exits 0 (constructs and starts the app without error).

- [ ] **Step 3: Commit**

```bash
git add tests/snapshot_apps/seeded_app.py
git commit -m "test: deterministic seeded app launcher for snapshots"
```

### Task 5.2: Snapshot tests for main view and modals

**Files:**
- Create: `tests/test_snapshots.py`

- [ ] **Step 1: Write the snapshot tests**

```python
# ABOUTME: Visual regression snapshots via pytest-textual-snapshot.
# ABOUTME: Determinism comes from the seeded in-memory DB + stub provider in seeded_app.py.
from pathlib import Path

APP = str(Path(__file__).parent / "snapshot_apps" / "seeded_app.py")


def test_main_view(snap_compare):
    assert snap_compare(APP, terminal_size=(100, 30))


def test_detail_with_summary(snap_compare):
    # Select the first bookmark row so the detail panel renders a (stub) summary.
    assert snap_compare(APP, terminal_size=(100, 30), press=["tab", "tab", "enter"])


def test_add_modal(snap_compare):
    assert snap_compare(APP, terminal_size=(100, 30), press=["a"])


def test_search_modal(snap_compare):
    assert snap_compare(APP, terminal_size=(100, 30), press=["slash"])


def test_delete_modal(snap_compare):
    assert snap_compare(APP, terminal_size=(100, 30), press=["tab", "tab", "d"])
```

- [ ] **Step 2: Generate baseline snapshots**

Run: `uv run pytest tests/test_snapshots.py --snapshot-update -v`
Expected: tests "pass" creating baselines. Open the generated report (path printed by pytest) and **visually confirm** the main view shows the three panes with Catppuccin Mocha colors, the detail test shows a summary line, and each modal renders centered. If the `press` sequences land on the wrong widget, adjust the key lists (e.g. number of `tab`s) until each snapshot shows the intended state, then re-run with `--snapshot-update`.

- [ ] **Step 3: Verify snapshots are stable on re-run**

Run: `uv run pytest tests/test_snapshots.py -v`
Expected: PASS (5 passed) with no diffs — proves determinism.

- [ ] **Step 4: Commit**

```bash
git add tests/test_snapshots.py tests/__snapshots__
git commit -m "test: visual regression snapshots for main view and modals"
```

### Task 5.3: Final sweep — full suite, lint, types, docs

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run the full quality gate**

Run: `uv run pytest -v && uv run ruff check . && uv run ty check`
Expected: all tests pass, ruff clean, ty clean. Fix any findings before continuing.

- [ ] **Step 2: Update `README.md`**

Rewrite the Requirements/Getting Started sections to reflect uv, the `RAINDROP` and `ANTHROPIC_API_KEY` env vars, lazy summaries (no more slow first launch), and the new commands:

```markdown
## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Getting Started

1. Clone the repo.
2. `uv sync` to install dependencies.
3. Set `RAINDROP` to your Raindrop.io API token and `ANTHROPIC_API_KEY` to your Anthropic key.
4. `just run` (or `uv run textual run --dev avocet/app.py`).
5. Use the arrow keys to move between collections and bookmarks. Press Enter on a bookmark
   to view its details (a Claude summary is generated on first view and cached). Press `o` to
   open it in the browser, `/` to search, `a`/`e`/`d` to add/edit/delete, and `ctrl+p` for the
   command palette (including theme switching).

Summaries are generated lazily the first time you open each bookmark, so startup is instant.
```

- [ ] **Step 3: Update `CLAUDE.md`**

Replace the Poetry/OpenAI/LangChain descriptions with the uv toolchain, the new module map (`app.py`, `raindrop_api.py`, `database_manager.py`, `models.py`, `summary.py`, `screens.py`), the `SummaryProvider` seam, lazy-summary behavior, `ANTHROPIC_API_KEY`, and the three test layers (unit / interaction via `run_test`+`Pilot` / visual via `pytest-textual-snapshot`). Keep the bare-import vs package-import note.

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update README and CLAUDE.md for the modernized app"
```

---

## Self-review notes

- **Spec coverage:** uv migration (1.1–1.2), Python 3.12+ (1.1), pruned deps incl. removing langchain/openai/chroma (1.1, 2.4), Textual 8.x three-pane UI (3.1), Catppuccin Mocha + runtime switch + persistence (3.1, 3.3), lazy summaries via provider seam (2.4, 3.1), pagination + nested/system collections fixes with tests (2.3), search/tag/add/edit/delete (4.1–4.3), three test layers incl. snapshots (2.x unit, 3.x/4.x interaction, 5.x visual), repo hygiene/remove committed DB (1.3), README/CLAUDE.md (5.3). All covered.
- **Determinism for visual tests:** every snapshot uses the seeded in-memory DB + `StubSummaryProvider` (5.1) — the load-bearing decision from the spec.
- **Type consistency:** `DatabaseManager` methods (`upsert_collection`, `upsert_raindrops`, `get_collections`, `get_raindrops_by_collection_id`, `get_raindrop`, `set_summary`, `remove_raindrop`, `get_setting`, `set_setting`, `touch_last_update`, `get_last_update`) are defined in 2.2 and used consistently in 3.x/4.x. `SummaryProvider.summarize`, `AddResult`, `EditResult` are used as defined. `RaindropAPI` method names match between 2.3 and the app/fakes.
- **Known follow-up (not a blocker):** `action_search` wires its callback in 4.3 Step 3 (the `push_screen(SearchScreen(), on_close)` line) — the builder must include the callback argument, as called out in the step.
