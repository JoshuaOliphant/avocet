# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Avocet is a Textual TUI for browsing [Raindrop.io](https://raindrop.io) bookmarks. It syncs collections and bookmarks from the Raindrop API into a local SQLite cache, and generates a concise summary of a bookmark with Claude the first time you open it (cached thereafter). Selecting a bookmark opens it in the browser.

## Toolchain (uv + just)

This repo is managed with **uv** (PEP 621 `pyproject.toml`, real `uv.lock`), with tasks fronted by a **justfile**.

```bash
just install         # uv sync
just run             # uv run textual run --dev avocet/app.py
just test            # uv run pytest
just lint            # uv run ruff check .
just typecheck       # uv run ty check
just console         # uv run textual console (live debug log in a second terminal)
just snapshot-update # uv run pytest --snapshot-update (regenerate visual baselines)
```

Run a single test:

```bash
uv run pytest tests/test_raindrop_api.py
uv run pytest tests/test_raindrop_api.py::test_get_raindrops_paginates
uv run pytest -k collection
```

CI (`.github/workflows/python-app.yml`) runs `ruff check`, `ty check`, and `pytest` on Python 3.12 and 3.13 via uv, on pushes/PRs to `main`.

## Required environment variables

- `RAINDROP` — Raindrop.io API token (read by `RaindropAPI.__init__` via `os.environ["RAINDROP"]`; **the name is `RAINDROP`, not `RAINDROP_TOKEN`**).
- **One** summary-provider key: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.
- Optional `AVOCET_SUMMARY_PROVIDER` (`anthropic`|`openai`) and `AVOCET_SUMMARY_MODEL` (model id).

**Provider selection** lives in `summary.py`: `resolve_provider_name()` returns the explicit `AVOCET_SUMMARY_PROVIDER` if set, else auto-detects from whichever key is present (anthropic preferred when both are). `create_summary_provider()` builds the matching real provider (`ClaudeSummaryProvider` / `OpenAISummaryProvider`), applying `AVOCET_SUMMARY_MODEL` over the per-provider default (`CLAUDE_MODEL` / `OPENAI_MODEL`). Both real providers share `_LLMSummaryProvider` (page fetch + prompt orchestration) and only implement `_complete()`. `Avocet.__init__` calls the factory when no provider is injected.

These may be supplied via a `.env` file: `main()` calls `_load_environment()` (in `app.py`), which runs `python-dotenv`'s `load_dotenv(find_dotenv(usecwd=True))`, then requires `RAINDROP` and the selected provider's key, raising `SystemExit` with a clear message otherwise. Real environment variables take precedence over `.env` (`override=False`). `.env` is gitignored; `.env.example` is the tracked template.

The SQLite cache lives under the platform cache dir (`platformdirs.user_cache_dir("avocet")`), not the working directory.

## Architecture

Modules under `avocet/`, orchestrated by the Textual app:

```
app.py      (Avocet(App)) — three-pane UI + lifecycle; constructed with injected dependencies
   ├── raindrop_api.py     (RaindropAPI)      async httpx client for the Raindrop REST API
   ├── database_manager.py (DatabaseManager)  SQLAlchemy 2.0 wrapper over the local SQLite cache + settings
   │      └── models.py    (Collection / Raindrop / Update)  typed declarative models
   ├── summary.py          (SummaryProvider / ClaudeSummaryProvider / StubSummaryProvider)
   └── screens.py          (Add/Edit/Delete/Search/TagFilter ModalScreens + result dataclasses)
```

**Local DB is the source of truth for the UI.** The TUI reads exclusively from `DatabaseManager`. `RaindropAPI` and the summary provider are touched only by background workers (`@work`), never directly in response to navigation.

**Dependency injection.** `Avocet(db=None, summary_provider=None, api=None)` — defaults build a real `DatabaseManager` (platform cache dir) and `ClaudeSummaryProvider`. Tests inject a seeded in-memory `DatabaseManager` and a `StubSummaryProvider`, so they never hit the network. This seam is what makes interaction and snapshot tests deterministic.

**UI.** Three panes: a collections `ListView` (`#collections`), a bookmarks `DataTable` (`#bookmarks`), and a detail panel (`#detail` with `#detail-title`/`#detail-meta`/`#detail-summary`). Selecting a collection repopulates the table from the DB; selecting a row shows detail. Catppuccin Mocha theme is registered as the default and persisted to the DB settings table via `watch_theme`; the command palette switches themes at runtime. Keybindings: `o` open, `r` refresh/sync, `/` search, `a` add, `e` edit, `d` delete, `f` filter tag.

**Lazy summaries.** A summary is generated on explicit row selection (Enter), not on highlight, inside a `@work(exclusive=True)` worker — so arrowing through rows never fires a storm of API calls. The result is cached in SQLite (`DatabaseManager.set_summary`) and reused forever. `upsert_raindrops` deliberately preserves an existing summary on re-sync (never clobbers it).

**Sync.** `action_refresh` runs the `_sync` worker: fetch collections + their raindrops from `RaindropAPI` and upsert into the DB, then reload the UI.

**Data-correctness details (these were bugs in the old code, now fixed and tested).** `RaindropAPI.get_raindrops_by_collection_id` **paginates** (`perpage=50`, loop until a short page) instead of returning only the first ~25. `get_collections` merges root `/collections`, nested `/collections/childrens`, and a synthetic system "All" collection (`_id: 0`), so every bookmark is reachable.

## Imports

All modules under `avocet/` use **package imports** (`from avocet.models import ...`). The package is genuinely installable (hatchling wheel + `avocet = "avocet.app:main"` console script). The pytest `pythonpath` is `[".", "tests"]`. Keep new internal imports in the `avocet.` form — do not introduce bare `from models import ...` style (it breaks `ty` and a real install, and can cause SQLAlchemy double-registration).

## Testing (three layers)

- **Unit.** `tests/test_raindrop_api.py` mocks HTTP with `pytest-httpx` (the `httpx_mock` fixture) including multi-page responses that prove pagination assembles all items. `tests/test_database_manager.py` and `tests/test_models.py` use a real in-memory SQLite engine: `create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)` + `create_tables()`. `StaticPool` is required so the schema created in the fixture persists across the sessions the manager opens — no mocks.
- **Interaction.** `tests/test_app_*.py` drive the app through Textual's `App.run_test()` / `Pilot` API with a seeded in-memory DB and `StubSummaryProvider`, asserting real state changes (collection switch, lazy summary, modal flows, sync).
- **Visual regression.** `tests/test_snapshots.py` uses `pytest-textual-snapshot` (`snap_compare`) against `tests/snapshot_apps/seeded_app.py` (a deterministic seeded launcher). Baselines live under `tests/__snapshots__/`. Regenerate with `just snapshot-update` only after visually confirming an intended UI change.

`asyncio_mode = "auto"` is set, so `async def test_*` runs without a marker.
