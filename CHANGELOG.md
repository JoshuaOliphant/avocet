# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-30

A ground-up modernization of Avocet. The app keeps its purpose — a terminal UI for
browsing Raindrop.io bookmarks with AI-generated summaries — but the toolchain,
architecture, UI, and test suite have all been rebuilt.

### Added
- **Three-pane Textual UI**: collections sidebar, sortable bookmarks table, and a
  detail panel, on Textual 8.x.
- **Catppuccin Mocha** theme by default, with runtime theme switching via the
  command palette; the chosen theme persists across launches.
- **Bookmark management**: add, edit, delete, search, and tag filtering via modal
  screens, wired through to the Raindrop API.
- **Choice of summary provider**: summaries can be generated with **Anthropic
  Claude** or **OpenAI**. The provider is auto-detected from whichever API key is
  present (Anthropic wins if both); override with `AVOCET_SUMMARY_PROVIDER` and the
  model with `AVOCET_SUMMARY_MODEL`.
- **Lazy, cached summaries**: a summary is generated the first time you open a
  bookmark and cached in SQLite, so startup is instant.
- **`.env` support**: credentials can be supplied via a `.env` file (see
  `.env.example`); real environment variables take precedence.
- **Three-layer test suite**: unit (pytest-httpx + real in-memory SQLite),
  interaction (Textual `run_test`/`Pilot`), and visual-regression snapshots
  (pytest-textual-snapshot).

### Changed
- **Toolchain**: migrated from Poetry to **uv**; targets **Python 3.12+**.
- **Linting/types**: replaced flake8 with **ruff** and added the **ty** type
  checker; CI runs ruff, ty, and pytest on Python 3.12 and 3.13.
- **Data layer**: rebuilt on SQLAlchemy 2.0 typed models with a `DatabaseManager`
  whose upserts preserve cached summaries across syncs.

### Fixed
- **Bookmark pagination**: the Raindrop client now fetches all pages instead of
  silently stopping at the first ~25 bookmarks per collection.
- **Nested and system collections**: child collections and the virtual "All" view
  are now included, so every bookmark is reachable.
- **"All" collection**: now a virtual view over every bookmark rather than a stored
  collection, so it can no longer clobber a bookmark's real collection.
- **Add bookmark title**: the Add dialog has a title field; a typed title is sent to
  Raindrop instead of leaving the URL as the title.
- **Search results**: searching now shows only the matching bookmarks instead of
  re-rendering the whole collection.
- **Error handling**: HTTP errors surface to the user instead of silently producing
  empty results; background workers report failures via notifications.

### Removed
- The OpenAI/LangChain/Chroma summarization stack was replaced by direct provider
  integrations. (OpenAI summarization itself remains available — see Added.)
