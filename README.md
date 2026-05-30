[![Python application](https://github.com/JoshuaOliphant/avocet/actions/workflows/python-app.yml/badge.svg)](https://github.com/JoshuaOliphant/avocet/actions/workflows/python-app.yml)

# Avocet

Avocet is a TUI for browsing your [Raindrop.io](https://raindrop.io) bookmarks. It is written in Python with the [Textual](https://textual.textualize.io) framework. It syncs your collections and bookmarks into a local SQLite cache, generates a concise summary of a bookmark with [Claude](https://www.anthropic.com/claude) the first time you open it (cached thereafter), and opens links in your default browser.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Getting Started

1. Clone the repo.
2. `uv sync` (or `just install`) to install dependencies.
3. Provide the required credentials, either as environment variables or in a `.env`
   file (copy `.env.example` to `.env` and fill it in — exported variables take
   precedence over `.env`):
   - `RAINDROP` — your Raindrop.io API token (from app.raindrop.io/settings/integrations).
   - `ANTHROPIC_API_KEY` — your Anthropic API key (used to summarize bookmarks).
4. `just run` (or `uv run textual run --dev avocet/app.py`).
5. Navigate with the arrow keys. Move focus between the collections sidebar and the
   bookmarks table; press Enter on a bookmark to view its details — a Claude summary is
   generated on first view and cached. Useful keys: `o` open in browser, `/` search,
   `a`/`e`/`d` add/edit/delete, `f` filter by tag, `r` refresh from Raindrop, and
   `ctrl+p` for the command palette (including runtime theme switching). `ctrl+c` quits.

Summaries are generated lazily the first time you open each bookmark, so startup is instant.

## Development

Common tasks (see the [justfile](./justfile) for all of them):

```bash
just test            # uv run pytest
just lint            # uv run ruff check .
just typecheck       # uv run ty check
just snapshot-update # regenerate visual snapshot baselines after a UI change
```

The test suite has three layers: unit tests (Raindrop API client and database manager),
interaction tests driven through Textual's `run_test`/`Pilot`, and visual-regression
snapshot tests via `pytest-textual-snapshot`.

![Screenshot](./media/Screenshot.png)
