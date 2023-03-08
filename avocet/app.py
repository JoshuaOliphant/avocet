from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Input, Static, Header, Footer, Button, Label, ListItem, ListView
from textual import events, log
from textual.containers import Container 

from rich.markdown import Markdown

from raindrop import Raindrop


class URLInput(Static):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="https://", id="input")

class CollectionItem(ListItem):
    def __init__(self, id):
        self.id = id
        super().__init__(id=id)

class Collection(ListView):

    def __init__(self, id):
        self._id = id
        self.raindrop = Raindrop()
        self.items = self.raindrop.getCollections()
        self.list_items = []
        for key, value in self.items.items():
            self.list_items.append(ListItem(Label('{} {}'.format(key, value['count'])), id=key))
        super().__init__(*self.list_items)
    
    def get_raindrops_by(self, name: str):
        return self.items[name]

class Previews(ListView):

    def __init__(self, id):
        self._id = id
        self.raindrop = Raindrop()
        self.items = self.raindrop.getRaindropsBy('30350988')
        self.list_items = [ListItem(Label('{} {}'.format(item['title'], item['excerpt']), id="raindrop")) for item in self.items]
        super().__init__(*self.list_items)
    
    def update_preview(self, id: str):
        self.clear()
        self.items = self.raindrop.getRaindropsBy(id)
        log(f"items: {self.items}")
        for item in self.items:
            self.append(ListItem(Label('{} {}'.format(item['title'], item['excerpt']))))
        # self.list_items = [ListItem(Label('{} {}'.format(item['title'], item['excerpt']), id="raindrop")) for item in self.items]

class Info(App):
    CSS_PATH = "avocet.css"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            URLInput(),
            Collection(id="Collection"),
            Previews(id="Previews")
        )
        
    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_list_view_selected(self, event):
        collections = self.query_one(Collection)
        collection = collections.get_raindrops_by(event.item.id)
        previews = self.query_one(Previews)
        previews.update_preview(collection["id"])

if __name__ == "__main__":
    app = Info()
    app.run()
