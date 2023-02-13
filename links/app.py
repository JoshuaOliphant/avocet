from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Header, Footer, Button, Label, ListItem, ListView
from textual import events
from textual.containers import Container 

from rich.markdown import Markdown

from raindrop import Raindrop


class URLInput(Static):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="https://", id="input")

class Collection(Static):

    def compose(self) -> ComposeResult:
        raindrop = Raindrop()
        items = raindrop.getCollections()
        items = [ListItem(Label('{} {}'.format(item['title'], item['count']), id="title")) for item in items]
        yield ListView(*items)

class Info(App):
    CSS_PATH = "links.css"
    BINDINGS = [
        ("a", "add_link", "add link"),
        ("tab", "toggle_class('#Collection', '-active')", "toggle sidebar")
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            URLInput(),
            Collection(id="Collection") 
        )
        
    def on_mount(self) -> None:
        self.query_one(Input).focus()
        
    #def on_input_submitted(self, event: Input.Submitted) -> None:
        #self.query_one("#link_entered", Static).update(Markdown(str(links)))

if __name__ == "__main__":
    app = Info()
    app.run()
