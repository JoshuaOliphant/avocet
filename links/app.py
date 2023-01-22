from textual.app import App, ComposeResult
from textual.containers import Content
from textual.widgets import Input, Static, Header, Footer, Button, Label, ListItem, ListView
from textual import events
from textual.containers import Container, Vertical

from rich.markdown import Markdown

from contextlib import closing

import sqlite3

connection = sqlite3.connect("links.db")
cursor = connection.cursor()
# cursor.execute("CREATE TABLE links (link TEXT)")

class AddLink(Static):
    def compose(self) -> ComposeResult:
        yield Label("URL", id="url")
        yield Input(placeholder="Enter a link", id="input")

class ExistingLinks(Static):
    def compose(self) -> ComposeResult:
        links = cursor.execute("SELECT * FROM links").fetchall()
        # list_items = tuple([ListItem(Label(str(link[0] for link in links)))])
        # list_items = [ListItem(Label(str(link[0][0]))) for link in links]
        # yield ListView(tuple(ListItem(Label(str(links[0][0])))))
        list_items = [ListItem(Label(link[0])) for link in links]
        yield ListView(
            *list_items
        )

class Info(App):
    CSS_PATH = "links.css"
    BINDINGS = [("a", "add_link", "add link")]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            AddLink(),
            ExistingLinks()
        )
        
    def on_mount(self) -> None:
        self.query_one(Input).focus()
        
    def on_input_submitted(self, event: Input.Submitted) -> None:
        link = self.query_one(Input).value
        cursor.execute(f"INSERT INTO links VALUES ('{link}')")
        connection.commit()
        links = cursor.execute("SELECT * FROM links").fetchall()
        self.query_one("#link_entered", Static).update(Markdown(str(links)))

if __name__ == "__main__":
    app = Info()
    app.run()