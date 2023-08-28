import asyncio
import os
import time
import webbrowser
from textual import on, work, log
from textual.app import App, ComposeResult
from textual.containers import Center
from textual.widgets import OptionList, ProgressBar, Label
from textual.widgets.option_list import Option
from sqlalchemy import create_engine
from database_manager import DatabaseManager
from raindrop_api import RaindropAPI

class Avocet(App):

    CSS_PATH = "avocet.tcss"

    def compose(self) -> ComposeResult:
        with Center():
            yield Label("Loading...")
            yield ProgressBar(total=100)
        with Center():
            yield OptionList(id="collection_option_list")
            yield OptionList(id="raindrop_option_list")

    async def on_mount(self) -> None:
        self.startup()

    @work
    async def startup(self):
        # Check if the database exists
        start_time = time.time()
        db_name = os.environ.get("DB_NAME", "avocet")
        db_path = f'{db_name}.sqlite'
        raindrop_api = RaindropAPI()

        if not os.path.exists(db_path):
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.database_manager = DatabaseManager(self.engine)
            self.database_manager.create_tables()
            collection_data_list = await raindrop_api.get_collections()
            self.query_one(ProgressBar).update(total=len(collection_data_list))
            for collection_data in collection_data_list:
                self.database_manager.add_collection(collection_data)
                raindrop_data_list = await raindrop_api.get_raindrops_by_collection_id(collection_data["_id"])
                self.database_manager.add_raindrops(raindrop_data_list, collection_data["_id"])
                self.query_one(ProgressBar).advance(1)
        else:
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.database_manager = DatabaseManager(self.engine)
        self.query_one(ProgressBar).remove()
        self.query_one(Label).remove()
        self.initialize_view()
        end_time = time.time()
        log(f"Startup time: {start_time-end_time}")

    def initialize_view(self):
        collections = self.database_manager.get_collections()
        for collection in collections:
            collection_options = [Option(prompt=collection.title, id=collection.id)]
            collection_option_list = self.query_one("#collection_option_list")
            collection_option_list.add_options(collection_options)
        if collections:
            raindrops = self.database_manager.get_raindrops_by_collection_id(collections[0].id)
        else:
            raindrops = []
        raindrop_options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in raindrops]
        raindrop_option_list = self.query_one("#raindrop_option_list")
        raindrop_option_list.add_options(raindrop_options)

    @on(OptionList.OptionSelected, selector="#collection_option_list")
    def select_collection(self, event: OptionList.OptionSelected):
        collection_id = event.option.id
        raindrops = self.database_manager.get_raindrops_by_collection_id(collection_id)
        options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in raindrops]
        option_list = self.query_one("#raindrop_option_list")
        option_list.clear_options()
        option_list.add_options(options)

    @on(OptionList.OptionSelected, selector="#raindrop_option_list")
    def select_raidrop(self, event: OptionList.OptionSelected):
        log("selected")
        raindrop_id = event.option.id
        raindrop = self.database_manager.get_raindrop_by_raindrop_id(raindrop_id)
        webbrowser.open(raindrop.link)


if __name__ == "__main__":
    avocet = Avocet()
    avocet.run()
