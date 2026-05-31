# ABOUTME: Avocet — a Textual TUI for browsing Raindrop.io bookmarks (three-pane layout).
# ABOUTME: The local DB is the source of truth; summaries are generated lazily on row selection.
from __future__ import annotations

import os
import webbrowser

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, Label, ListItem, ListView, Static

from avocet.database_manager import DatabaseManager
from avocet.models import Raindrop
from avocet.raindrop_api import (
    ALL_COLLECTION_ID,
    SYSTEM_COLLECTION_IDS,
    RaindropAPI,
    RaindropClient,
)
from avocet.screens import (
    AddBookmarkScreen,
    AddResult,
    ConfirmDeleteScreen,
    EditBookmarkScreen,
    EditResult,
    SearchScreen,
    TagFilterScreen,
)
from avocet.summary import (
    SUMMARY_PROVIDER_KEYS,
    SummaryProvider,
    create_summary_provider,
    resolve_provider_name,
)

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


def _fmt_tags(tags: list[str]) -> str:
    return " ".join(f"#{t}" for t in tags)


def _default_db() -> DatabaseManager:
    from pathlib import Path

    from platformdirs import user_cache_dir

    cache_dir = Path(user_cache_dir("avocet"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{cache_dir / 'avocet.sqlite'}")
    manager = DatabaseManager(engine=engine)
    manager.create_tables()
    return manager


class CollectionItem(ListItem):
    """A sidebar list item that carries the id of the collection it represents."""

    def __init__(self, collection_id: int, label: str) -> None:
        super().__init__(Label(label))
        self.collection_id = collection_id


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
        api: RaindropClient | None = None,
    ) -> None:
        super().__init__()
        self.db = db or _default_db()
        self.summary_provider = summary_provider or create_summary_provider()
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
        # The guard is needed because Textual's reactive machinery can call
        # watch_theme before Avocet.__init__ has assigned self.db.
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
        listview.append(CollectionItem(ALL_COLLECTION_ID, "All"))
        for collection in self.db.get_collections():
            listview.append(CollectionItem(collection.id, collection.title or "(untitled)"))
        self._populate_table(ALL_COLLECTION_ID)

    def _populate_table(self, collection_id: int, tag: str | None = None) -> None:
        self._current_collection_id = collection_id
        if collection_id == ALL_COLLECTION_ID:
            rows = self.db.get_all_raindrops()
        else:
            rows = self.db.get_raindrops_by_collection_id(collection_id)
        if tag:
            rows = [r for r in rows if tag in r.tags]
        self._render_rows(rows)

    def _render_rows(self, rows: list[Raindrop]) -> None:
        # Render an explicit list of raindrops into the bookmarks table. Used for
        # collection views (via _populate_table) and for search results, which
        # must show only the matches rather than the whole collection.
        table = self.query_one("#bookmarks", DataTable)
        table.clear()
        self._row_to_raindrop.clear()
        for raindrop in rows:
            row_key = str(raindrop.id)
            created = raindrop.created.strftime("%Y-%m-%d") if raindrop.created else ""
            table.add_row(raindrop.title or "", _fmt_tags(raindrop.tags), created, key=row_key)
            self._row_to_raindrop[row_key] = raindrop.id

    @on(ListView.Selected, "#collections")
    def _collection_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, CollectionItem):
            self._populate_table(event.item.collection_id)

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
        tags = _fmt_tags(raindrop.tags)
        self.query_one("#detail-meta", Static).update(f"{tags}  ·  {raindrop.link or ''}")
        if raindrop.summary:
            self.query_one("#detail-summary", Static).update(raindrop.summary)
        else:
            self.query_one("#detail-summary", Static).update("Generating summary…")
            self._generate_summary(raindrop_id)

    @work(exclusive=True)
    async def _generate_summary(self, raindrop_id: int) -> None:
        try:
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
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self.query_one("#detail-summary", Static).update(f"Summary unavailable: {exc}")

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
        try:
            if self.api is None:
                self.api = RaindropAPI()
            collections = await self.api.get_collections()
            for collection in collections:
                # System views ("All", "Unsorted") are virtual — never store them.
                if collection["_id"] in SYSTEM_COLLECTION_IDS:
                    continue
                self.db.upsert_collection(collection)
                items = await self.api.get_raindrops_by_collection_id(collection["_id"])
                self.db.upsert_raindrops(items, collection["_id"])
            self._load_collections()
            self.notify("Synced from Raindrop.io")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self._load_collections()
            self.notify(f"Sync failed: {exc}", severity="error")

    def action_search(self) -> None:
        def on_close(query: str | None) -> None:
            if query and self._current_collection_id is not None:
                self._do_search(self._current_collection_id, query)

        self.push_screen(SearchScreen(), on_close)

    @work(exclusive=True, group="search")
    async def _do_search(self, collection_id: int, query: str) -> None:
        try:
            if self.api is None:
                self.api = RaindropAPI()
            items = await self.api.get_raindrops_by_collection_id(collection_id, search=query)
            self.db.upsert_raindrops(items, collection_id)
            # Show only the matches (read back from the DB in one query so they
            # carry their real collection_id), not the whole collection.
            self._render_rows(self.db.get_raindrops_by_ids([item["_id"] for item in items]))
            self.notify(f"{len(items)} result(s) for '{query}'")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self.notify(f"Search failed: {exc}", severity="error")

    def action_add(self) -> None:
        if self._current_collection_id is None:
            return

        def on_close(result: AddResult | None) -> None:
            if result is not None:
                self._do_add(result)

        self.push_screen(AddBookmarkScreen(self._current_collection_id), on_close)

    @work(exclusive=True, group="crud")
    async def _do_add(self, result: AddResult) -> None:
        try:
            if self.api is None:
                self.api = RaindropAPI()
            item = await self.api.add_raindrop(
                result.link, result.collection_id, result.tags, result.title
            )
            self.db.upsert_raindrops([item], result.collection_id)
            self._populate_table(result.collection_id)
            self.notify("Bookmark added")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self.notify(f"Add failed: {exc}", severity="error")

    def action_edit(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop is None:
            return

        def on_close(result: EditResult | None) -> None:
            if result is not None:
                self._do_edit(result)

        self.push_screen(
            EditBookmarkScreen(raindrop.id, raindrop.title or "", raindrop.tags), on_close
        )

    @work(exclusive=True, group="crud")
    async def _do_edit(self, result: EditResult) -> None:
        try:
            if self.api is None:
                self.api = RaindropAPI()
            item = await self.api.update_raindrop(
                result.raindrop_id, {"title": result.title, "tags": result.tags}
            )
            if self._current_collection_id is not None:
                self.db.upsert_raindrops([item], self._current_collection_id)
                self._populate_table(self._current_collection_id)
            self.notify("Bookmark updated")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self.notify(f"Edit failed: {exc}", severity="error")

    def action_delete(self) -> None:
        raindrop = self._selected_raindrop()
        if raindrop is None:
            return

        def on_close(confirmed: bool | None) -> None:
            if confirmed:
                self._do_delete(raindrop.id)

        self.push_screen(ConfirmDeleteScreen(raindrop.title or ""), on_close)

    @work(exclusive=True, group="crud")
    async def _do_delete(self, raindrop_id: int) -> None:
        try:
            if self.api is None:
                self.api = RaindropAPI()
            await self.api.delete_raindrop(raindrop_id)
            self.db.remove_raindrop(raindrop_id)
            if self._current_collection_id is not None:
                self._populate_table(self._current_collection_id)
            self.notify("Bookmark deleted")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the user
            self.notify(f"Delete failed: {exc}", severity="error")

    def action_filter_tag(self) -> None:
        def on_close(tag: str | None) -> None:
            if tag is not None:
                self.apply_tag_filter(tag)

        self.push_screen(TagFilterScreen(), on_close)

    def apply_tag_filter(self, tag: str) -> None:
        if self._current_collection_id is None:
            return
        self._populate_table(self._current_collection_id, tag=tag)


def _load_environment() -> None:
    # Load a local .env (searching up from the working directory) so credentials
    # can live in a file instead of the shell. Real environment variables win
    # over .env values (load_dotenv defaults to override=False).
    load_dotenv(find_dotenv(usecwd=True))
    if "RAINDROP" not in os.environ:
        raise SystemExit(
            "RAINDROP is not set. Export it or add it to a .env file "
            "(your Raindrop.io API token)."
        )
    try:
        provider = resolve_provider_name()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    required_key = SUMMARY_PROVIDER_KEYS[provider]
    if required_key not in os.environ:
        raise SystemExit(
            f"{required_key} is not set. The '{provider}' summary provider needs it. "
            "Export it or add it to a .env file, or set AVOCET_SUMMARY_PROVIDER to a "
            "provider whose key you have."
        )


def main() -> None:
    _load_environment()
    Avocet().run()


if __name__ == "__main__":
    main()
