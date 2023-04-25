from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input, ListView, ListItem, Label
from textual.containers import Container
import webbrowser

from raindrop import Raindrop

def collection_to_list_items(collections: map) -> list:
    # create a list of list items from the list of collections
    if collections is None:
        return []
    return [ListItem
            (Label('{} {}'.format(key, value['count'])),
                name="collection_list", id=key)
            for key, value in collections.items()]

def raindrops_to_list_items(raindrops: map) -> list:
    items = []
    for key, value in raindrops.items():
        try:
            title = value['title']
            excerpt = value['excerpt']
            items.append(ListItem(Label(f"{title} | {excerpt}"),
                                  name="raindrop_list", id=f"raindrop-{key}"))
        except Exception as e:
            print(e)
    return items

class URLInput(Static):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="https://", id="input")

class Avocet(App):
    CSS_PATH = "avocet.css"

    raindrop = Raindrop()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield URLInput(id="url_input")
            self.collection_map = self.raindrop.getCollections()
            self.raindrop_collections = collection_to_list_items(self.collection_map)
            yield ListView(*self.raindrop_collections, id="raindrop_collections")
            first_collection_id = next(iter(self.collection_map.values()))['id']
            self.raindrop_map = self.raindrop.getRaindropsBy(first_collection_id)
            yield ListView(*raindrops_to_list_items(self.raindrop_map), id="raindrop_previews")

    # Set focus to the input field.
    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def handle_raindrop_collection_selected(self, event: ListView.Selected):
        # get the collection that was selected
        raindrop_collection = self.collection_map[event.item.id]
        # get the list view that will show the raindrops in the collection
        raindrop_previews = self.query_one("#raindrop_previews")
        # clear the list view
        raindrop_previews.clear()
        # get the raindrops in the collection
        new_raindrops_collection = self.raindrop.getRaindropsBy(str(raindrop_collection["id"]))
        if new_raindrops_collection is not None:
            # convert the raindrops to list items
            new_raindrops = raindrops_to_list_items(new_raindrops_collection)
            # add the raindrops to the list view
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
        elif event.item.name == "raindrop_list":
            self.handle_raindrop_previews_selected(event)
        else:
            raise ValueError("Unknown list view selected")

    def on_input_submitted(self, event: Input.Submitted):
        url = event.value
        if url.startswith("http"):
            raindrop = {
                "link": url
            }
            self.raindrop.postRaindrop(raindrop)
        else:
            self.output = "Please enter a valid URL"


if __name__ == "__main__":
    app = Avocet()
    app.run()
