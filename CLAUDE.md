# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Avocet is a Textual TUI for browsing [Raindrop.io](https://raindrop.io) bookmarks. On first launch it pulls every collection and bookmark from the Raindrop API into a local SQLite database, then uses OpenAI (via LangChain) to generate a summary of each bookmark. Selecting a bookmark opens it in the browser.

## Toolchain (Poetry + just, not uv)

This repo is managed with **Poetry**, and tasks run through a **justfile** — despite the global preference for `uv`. The `uv.lock` at the root is a 3-line stub; `poetry.lock` is the real lockfile. Don't "migrate" to uv unless explicitly asked.

```bash
just install      # poetry install
just run          # poetry run textual run --dev avocet/app.py   (THE way to launch — see gotcha below)
just test         # poetry run pytest
just console      # textual console (live debug log; run in a second terminal while the app runs)
just shell        # poetry shell
```

Run a single test (no console-script shortcut needed):

```bash
poetry run pytest tests/test_raindrop_api.py
poetry run pytest tests/test_raindrop_api.py::test_get_collections
poetry run pytest -k collection
```

Lint matches CI: `poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`. CI (`.github/workflows/python-app.yml`) runs on Python 3.11 with flake8 + pytest on pushes/PRs to `main`.

## Required environment variables

- `RAINDROP` — Raindrop.io API token (read by `RaindropAPI.__init__` via `os.environ["RAINDROP"]`; **note the name is `RAINDROP`, not `RAINDROP_TOKEN`**).
- `OPENAI_API_KEY` — used by `AI` for summarization/embeddings.
- `DB_NAME` — optional, defaults to `avocet`; controls the SQLite filename `{DB_NAME}.sqlite`.

## Architecture

Four modules under `avocet/`, orchestrated by the Textual app:

```
app.py  (Avocet(App)) — UI + lifecycle orchestration
   ├── raindrop_api.py  (RaindropAPI)      async httpx client for the Raindrop REST API
   ├── database_manager.py (DatabaseManager) SQLAlchemy session wrapper over local SQLite
   │      └── models.py (Collection / Raindrop / Update)  declarative SQLAlchemy models
   └── ai.py (AI)        LangChain + OpenAI: fetch page, summarize, persist Chroma vectors
```

**Local DB is the source of truth for the UI.** The TUI reads exclusively from `DatabaseManager` (SQLAlchemy queries). `RaindropAPI` and `AI` are only touched during the `startup` worker to populate/refresh the DB — never in response to user navigation.

**Startup flow (`app.py`).** `on_mount` checks whether `{DB_NAME}.sqlite` exists, then kicks off the `@work`-decorated `startup` worker:
- **First run** (no DB file): `initialize_db` fetches all collections + their raindrops and stores them; then `add_text` calls `AI.html_to_markdown` for *every* bookmark to generate a summary. This is why the first launch is slow — one OpenAI round-trip per bookmark.
- **Subsequent runs**: `update_db` fetches only raindrops changed since `Update.last_update` (Raindrop `search=lastUpdate:<date>`), and `update_text` re-summarizes just those.

After populating, the progress bars are removed and `initialize_view` builds the two `OptionList`s (collections, raindrops) and the `MarkdownViewer`. Navigation handlers (`@on(OptionList.OptionSelected/OptionHighlighted)`) query the DB by id: highlighting a raindrop shows its `summary`; selecting one opens `raindrop.link` in the browser.

**Data model.** `Raindrop` mirrors the Raindrop API fields plus an extra `summary` column (the OpenAI-generated text — the one column that isn't from the API). The `Update` table holds a single row tracking the last sync time.

## Import-path gotcha

Modules use **bare imports** (`from database_manager import DatabaseManager`, `from models import ...`), not package-relative imports. These resolve only because `pyproject.toml` sets `pythonpath = [".", "avocet", "tests"]` for pytest, and because the app is launched via `textual run --dev avocet/app.py` (which runs the file with its directory on the path). Running `python -m avocet.app` will fail on imports. Preserve the bare-import style when adding modules under `avocet/`, or update `pythonpath` accordingly.

## Testing

- `tests/test_raindrop_api.py` mocks HTTP with `pytest-httpx` (the `httpx_mock` fixture) and sets a fake `RAINDROP` token via `monkeypatch` — tests never hit the real API.
- `tests/test_database_manager.py` builds a `DatabaseManager` over a real in-memory SQLite engine (`create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)` + `create_tables()`), so it exercises the manager's logic against a real database with real data — no mocks. `StaticPool` (plus `check_same_thread=False`) keeps one shared connection alive so the schema created in the fixture persists across the sessions the manager opens. Note these tests import package-style (`from avocet.database_manager import ...`) while `app.py` uses bare imports — both resolve through the `pythonpath` list.
- `asyncio_mode = "auto"` is set in `pyproject.toml`, so `async def test_*` runs without an explicit marker (the existing `@pytest.mark.asyncio` decorators are redundant but harmless).
