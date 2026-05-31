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
    title: str = ""
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
            yield Input(placeholder="title (optional, auto-fetched if blank)", id="title")
            yield Input(placeholder="tags, comma, separated", id="tags")
            yield Button("Add", id="confirm", variant="primary")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            link = self.query_one("#link", Input).value.strip()
            title = self.query_one("#title", Input).value.strip()
            tags = _parse_tags(self.query_one("#tags", Input).value)
            if link:
                self.dismiss(
                    AddResult(
                        link=link,
                        collection_id=self._collection_id,
                        title=title,
                        tags=tags,
                    )
                )
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
