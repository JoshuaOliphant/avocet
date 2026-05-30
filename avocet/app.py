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
from textual.widgets import DataTable, Footer, Header, Label, ListItem, ListView, Static

from avocet.database_manager import DatabaseManager
from avocet.models import Raindrop
from avocet.raindrop_api import RaindropAPI
from avocet.summary import ClaudeSummaryProvider, SummaryProvider

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
    from pathlib import Path

    from platformdirs import user_cache_dir

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
        self._current_collection_id: int | None = None

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

    def watch_theme(self, theme_name: str) -> None:
        # Persist the selected theme so it is restored on next launch.
        if getattr(self, "db", None) is not None:
            self.db.set_setting("theme", theme_name)

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
        self._current_collection_id = collection_id
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
        table = self.query_one("#bookmarks", DataTable)
        if table.row_count:
            cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if str(cell_key.row_key.value) == str(raindrop_id):
                self.query_one("#detail-summary", Static).update(summary)

    def _selected_raindrop(self) -> Raindrop | None:
        table = self.query_one("#bookmarks", DataTable)
        if table.row_count == 0:
            return None
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        raindrop_id = self._row_to_raindrop.get(str(cell_key.row_key.value))
        return self.db.get_raindrop(raindrop_id) if raindrop_id is not None else None

    def action_open_link(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop and raindrop.link:
            webbrowser.open(raindrop.link)

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
