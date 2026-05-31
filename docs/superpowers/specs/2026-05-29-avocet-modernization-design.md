# Avocet Modernization — Design

**Date:** 2026-05-29
**Status:** Approved (design phase)

## Goal

Modernize Avocet — a Textual TUI for Raindrop.io bookmarks — by upgrading the
entire dependency stack, rebuilding the UI on the latest Textual (8.2.7), fixing
latent data-correctness bugs, replacing the OpenAI/LangChain summarization stack
with a direct Anthropic Claude integration, and establishing a three-layer test
suite that includes visual regression testing.

## Decisions (locked)

| Axis | Decision |
| --- | --- |
| Package manager | Migrate Poetry → **uv** |
| Python target | **3.12+** (support 3.12 and 3.13) |
| Textual | **8.2.7** |
| Summarization | **Anthropic Claude** (replaces OpenAI/LangChain/Chroma) |
| Summary timing | **Lazy on explicit selection**, cached in SQLite |
| Layout | **Refined three-pane** (collections / bookmarks table / detail) |
| Theme | **Catppuccin Mocha** default, runtime-switchable via command palette |
| Features | Search, tag filtering, add, edit, delete |
| Data-loss bugs | **Fix** pagination + nested/system collections |

## Non-goals

- No web deployment (`textual-serve`) in this effort.
- No vector store / semantic search (Chroma is removed entirely).
- No Alembic migrations — the SQLite cache is treated as disposable and
  regenerable from the API (see Data Layer).

---

## Section 1 — Toolchain & Dependencies

Convert `pyproject.toml` from Poetry to **PEP 621 + `[tool.uv]`**, generate a real
`uv.lock`, delete `poetry.lock` and the 3-line `uv.lock` stub, and rewrite the
`justfile` and GitHub Actions workflow to use uv.

**Removed dependencies** (auditable diff):
`langchain`, `openai`, `chromadb`, `tiktoken`, `docarray`, `html2text`,
`flake8`, `asynctest`.

**Runtime dependencies:**
- `textual ^8.2`
- `httpx` (modern version)
- `sqlalchemy ^2.0`
- `anthropic` (new — Claude summaries)
- `platformdirs` (cache stored in the platform cache dir, not the cwd)

**Dev dependencies:**
- `pytest`, `pytest-asyncio`, `pytest-httpx`, `pytest-mock`
- `pytest-textual-snapshot` (visual regression)
- `ruff` (replaces flake8 — lint + format)
- `ty` (Astral type checker)

**Repo hygiene:**
- Delete the committed `avocet.sqlite` (217 KB of real bookmark data — stale
  schema + privacy smell).
- Add `*.sqlite` to `.gitignore`.
- CI runs `ruff check`, `ty`, and `pytest` on Python 3.12 and 3.13.

`justfile` targets become: `install` (`uv sync`), `run`
(`uv run textual run --dev avocet/app.py`), `test` (`uv run pytest`),
`console` (`uv run textual console`), `lint` (`uv run ruff check .`),
`typecheck` (`uv run ty check`).

---

## Section 2 — Data Layer (correctness-critical)

### `raindrop_api.py` — `RaindropAPI`

Async `httpx` client, used as an async context manager, `Authorization: Bearer`
auth read from the `RAINDROP` env var.

**Bugs fixed (not carried forward):**

1. **Pagination.** The current client fetches only the first page (~25 items)
   and silently drops the rest. The new client loops `?perpage=50&page=N` until
   a page returns fewer than `perpage` items.
2. **System + nested collections.** The current client only fetches top-level
   collections via `/collections`, missing child collections and the system
   collections. The new client also fetches `/collections/childrens` and
   includes system collection id `0` ("All") so every bookmark is reachable.

**Endpoints:**
- GET `/collections`, GET `/collections/childrens`
- GET `/raindrops/{collectionId}` (paginated; supports `search` param)
- GET `/raindrop/{id}`
- POST `/raindrop` (add)
- PUT `/raindrop/{id}` (edit)
- DELETE `/raindrop/{id}` (delete)

### `models.py` / `database_manager.py`

- SQLAlchemy 2.0 typed declarative models (`Mapped` / `mapped_column`).
- Tables: `Collection`, `Raindrop`, `Update` (last-sync marker).
- `Raindrop.summary` is **nullable** — filled lazily, cached forever once set.
- DB file lives under `platformdirs.user_cache_dir("avocet")` unless a `db_path`
  is supplied (tests supply an in-memory engine).
- The local SQLite DB is the **single source of truth for the UI**. The Raindrop
  API and Claude are touched only by background workers, never by navigation.

### Summary provider seam (enables deterministic tests)

Summarization sits behind a small protocol:

```python
class SummaryProvider(Protocol):
    async def summarize(self, raindrop: Raindrop) -> str: ...
```

- `ClaudeSummaryProvider` — real implementation using `AsyncAnthropic`
  (`messages.create`) with **prompt caching** on the system prompt. Fetches the
  bookmark's page text via `httpx`, sends it to Claude, returns a concise summary.
- `StubSummaryProvider` — deterministic, no network; returns fixed text. Used by
  the interaction and snapshot test suites.

The `Avocet` app is constructed with a `SummaryProvider` injected (defaulting to
`ClaudeSummaryProvider`), so tests can pass the stub and never hit the network.

---

## Section 3 — UI (Textual 8.x)

`Avocet(App)` with a CSS-grid layout:

- **Left:** collections `ListView` (system "All" first, then user collections
  with nesting indicated).
- **Main:** bookmarks `DataTable`, sortable, columns Title / Tags / Created.
- **Bottom:** detail panel showing the selected bookmark's title, excerpt, note,
  tags, link, and the lazily-generated Claude summary.

**Behavior:**
- Selecting a collection loads its raindrops from the DB into the table (via a
  worker that triggers an API sync if the collection is stale).
- **Lazy summaries done correctly:** a summary is generated on **explicit row
  selection (Enter)**, not on highlight, inside a `@work(exclusive=True)` worker
  so arrowing through rows never fires a storm of API calls. The result is
  written to SQLite and reused on every later view.
- `o` opens the selected bookmark's link in the browser.
- Default theme **Catppuccin Mocha**; the built-in command palette switches
  themes at runtime.
- Each feature is a `ModalScreen`: search (Raindrop full-text), tag filter, add
  (URL + collection + tags), edit (title/tags/collection), delete (confirm).
- Reactive attributes drive pane updates; panes communicate via custom messages.
  Full `BINDINGS` and a `Footer`.

---

## Section 4 — Testing (three layers)

### 1. Unit
- `raindrop_api` via `pytest-httpx` — including **multi-page mocked responses**
  to prove pagination assembles all items, and mocked `/collections/childrens`
  to prove nested collections are included.
- `database_manager` via a **real in-memory SQLite engine** with
  `create_engine("sqlite:///:memory:", poolclass=StaticPool)` + `create_tables()`
  (per the CLAUDE.md note — `StaticPool` keeps the schema across sessions). No
  mocks; real data in, real rows out.
- Summary logic via `StubSummaryProvider`.

### 2. Interaction
- `App.run_test()` + the `Pilot` API. Construct `Avocet` with a pre-seeded
  in-memory DB and `StubSummaryProvider`. Drive key presses / clicks and assert
  state: collection switch repopulates the table, Enter triggers a summary and
  fills the detail panel, modals open and submit, delete removes a row.

### 3. Visual regression
- `pytest-textual-snapshot` SVG snapshots via the `snap_compare` fixture.
- **Determinism by construction:** every snapshot runs the app with a
  **pre-seeded in-memory DB + `StubSummaryProvider`**, so rendered frames contain
  no live data and are stable across runs.
- Snapshots cover: the main three-pane view, the detail panel with a summary,
  each modal (search / add / edit / delete), and the Catppuccin Mocha theme.
- `pytest --snapshot-update` regenerates baselines after visual review.

---

## Section 5 — Phased delivery (each phase leaves the app runnable)

1. **Toolchain + dependency migration.** uv, pruned deps, ruff/ty, CI, justfile,
   gitignore, remove committed DB. Existing behavior still works.
2. **Data layer rewrite.** New `RaindropAPI` (pagination + nested/system
   collections), SQLAlchemy 2.0 models + `DatabaseManager`, summary provider
   seam. Full unit tests.
3. **New three-pane UI + theme.** Three panes, Tokyo Night, lazy-summary worker,
   command palette. Interaction tests.
4. **CRUD features.** Search, tag filtering, add, edit, delete modals + API
   wiring + tests.
5. **Visual test suite.** Snapshot tests for all views and modals.

---

## Risks & mitigations

- **Snapshot non-determinism** — mitigated by the injected stub provider +
  seeded in-memory DB (Section 4.3). This is the load-bearing design decision for
  the "test how it looks visually" requirement.
- **Lazy-summary call storms** — mitigated by summarizing on explicit selection
  only, inside an `exclusive=True` worker (Section 3).
- **Raindrop pagination/nesting** — explicitly fixed and unit-tested (Section 2).
- **Scope** — controlled by the five independently-runnable phases (Section 5).
