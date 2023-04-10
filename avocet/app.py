from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input, ListView, ListItem, Label, Footer
from textual.containers import Container
from textual import log
import webbrowser

from raindrop import Raindrop

def collection_to_list_items(collections: map):
    return [ListItem(Label('{} {}'.format(key, value['count'])), name="collection_list", id=key) for key, value in collections.items()]

def raindrops_to_list_items(raindrops: map):
    return [ListItem(Label('{} | {}'.format(value['title'], value['excerpt'])), name="raindrop_list", id=f"raindrop-{key}") for key, value in raindrops.items()]

class URLInput(Static):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="https://", id="input")

    def action_submit(self, url: str) -> None:
        log(f"URL: {url}")

class Avocet(App):
    CSS_PATH = "avocet.css"

    raindrop = Raindrop()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield URLInput()
            self.collection_map = self.raindrop.getCollections()
            self.raindrop_collections = collection_to_list_items(self.collection_map)
            yield ListView(*self.raindrop_collections, id="raindrop_collections")
            self.raindrop_map = self.raindrop.getRaindropsBy("30350988")
            yield ListView(*raindrops_to_list_items(self.raindrop_map), id="raindrop_previews")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def handle_raindrop_collection_selected(self, event: ListView.Selected):
        raindrop_collection = self.collection_map[event.item.id]
        id = raindrop_collection["id"]
        raindrop_previews = self.query_one("#raindrop_previews")
        raindrop_previews.clear()
        new_raindrops_collection = self.raindrop.getRaindropsBy(str(id))
        new_raindrops = raindrops_to_list_items(new_raindrops_collection)
        for raindrop in new_raindrops:
            raindrop_previews.append(raindrop)

    def handle_raindrop_previews_selected(self, event: ListView.Selected):
        raindrop_id = event.item.id.split("raindrop-", 1)[1]
        raindrop_map = self.raindrop.getRaindropBy(raindrop_id)
        link = raindrop_map[int(raindrop_id)]['link']
        webbrowser.open(link)

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item.name == "collection_list":
            self.handle_raindrop_collection_selected(event)
        if event.item.name == "raindrop_list":
            self.handle_raindrop_previews_selected(event)

    def on_input_submitted(self, event: Input.Submitted):
        url = event.value
        raindrop = {
            "link": url
        }
        self.raindrop.postRaindrop(raindrop)

if __name__ == "__main__":
    app = Avocet()
    app.run()
