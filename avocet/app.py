import webbrowser

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Static, Input, ListView, ListItem, Label
from textual import log

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

    _raindrop = Raindrop()

    url = reactive("")
    collection = reactive("")
    tags = reactive([])

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            with Vertical(id="vertical_inputs"):
                yield Input(placeholder="https://", id="url")
                yield Input(placeholder="collection name", id="collection")
                yield Input(placeholder="tags name", id="tags")
            with Horizontal(id="horizontal_lists"):
                self._collection_map = self._raindrop.getCollections()
                raindrop_collections = collection_to_list_items(self._collection_map)
                yield ListView(*raindrop_collections, id="raindrop_collections")
                first_collection_id = next(iter(self._collection_map.values()))['id']
                self._raindrop_map = self._raindrop.getRaindropsByCollectionID(first_collection_id)
                yield ListView(*raindrops_to_list_items(self._raindrop_map), id="raindrop_previews")

    def on_input_changed(self, event: Input.Changed) -> None:
        log(f"Input changed: {event.value}")
        if event.input.id == "url":
            log(f"URL changed: {event.value}")
            self.url = event.value
        elif event.input.id == "collection":
            log(f"Collection changed: {event.value}")
            self.collection = event.value
        elif event.input.id == "tags":
            log(f"Tags changed: {event.value}")
            self.tags.append(event.value)
        else:
            log(f"Unknown input changed: {event.input.id}")

    # Set focus to the input field.
    def on_mount(self) -> None:
        self.query_one("#url").focus()

    def handle_raindrop_collection_selected(self, event: ListView.Selected):
        log(f"Collection selected: {event.item.id}")
        # get the collection that was selected
        raindrop_collection = self._collection_map[event.item.id]
        # get the list view that will show the raindrops in the collection
        raindrop_previews = self.query_one("#raindrop_previews")
        # clear the list view
        raindrop_previews.clear()
        # get the raindrops in the collection
        new_raindrops_collection = self._raindrop.getRaindropsByCollectionID(str(raindrop_collection["id"]))
        if new_raindrops_collection is not None:
            # convert the raindrops to list items
            new_raindrops = raindrops_to_list_items(new_raindrops_collection)
            # add the raindrops to the list view
            for raindrop in new_raindrops:
                raindrop_previews.append(raindrop)

    def handle_raindrop_previews_selected(self, event: ListView.Selected):
        log(f"Raindrop selected: {event.item.id}")
        raindrop_id = event.item.id.split("raindrop-", 1)[1]
        raindrop_map = self._raindrop.getRaindropByRaindropId(raindrop_id)
        link = raindrop_map[int(raindrop_id)]['link']
        webbrowser.open(link)

    def on_list_view_selected(self, event: ListView.Selected):
        log(f"List view selected: {event.item.name}")
        if event.item.name == "collection_list":
            self.handle_raindrop_collection_selected(event)
        elif event.item.name == "raindrop_list":
            self.handle_raindrop_previews_selected(event)
        else:
            raise ValueError("Unknown list view selected")

    def on_input_submitted(self, event: Input.Submitted):
        log(f"Input submitted: {event.value}")
        log(f"Collections: {self.collection}")
        log(f"Tags: {self.tags}")
        log(f"URL: {self.url}")
        self._raindrop.postRaindrop(self.url, self.collection, self.tags)


if __name__ == "__main__":
    app = Avocet()
    app.run()
