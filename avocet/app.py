import os
import time
import webbrowser
from textual import on, work, log
from textual.app import App, ComposeResult
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from sqlalchemy import create_engine
from database_manager import DatabaseManager

class Avocet(App):

    CSS_PATH = "avocet.css"

    def compose(self) -> ComposeResult:
        yield OptionList(id="collection_option_list", )
        yield OptionList(id="raindrop_option_list")

    async def on_mount(self) -> None:
        self.startup()

    @work
    async def startup(self):
        # Check if the database exists
        start_time = time.time()
        db_name = os.environ.get("DB_NAME", "avocet")
        db_path = f'{db_name}.sqlite'

        if not os.path.exists(db_path):
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.database_manager = DatabaseManager(self.engine)
            self.database_manager.create_tables()
            await self.database_manager.add_collections()
        else:
            self.engine = create_engine(f'sqlite:///{db_path}')
            self.database_manager = DatabaseManager(self.engine)
        await self.initialize_view()
        end_time = time.time()
        log(f"Startup time: {start_time-end_time}")

    async def initialize_view(self):
        collections = await self.database_manager.get_collections()
        for collection in collections:
            collection_options = [Option(prompt=collection.title, id=collection.id)]
            collection_option_list = self.query_one("#collection_option_list")
            collection_option_list.add_options(collection_options)
        if collections:
            raindrops = await self.database_manager.get_raindrops_by_collection_id(collections[0].id)
        else:
            raindrops = []
        raindrop_options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in raindrops]
        raindrop_option_list = self.query_one("#raindrop_option_list")
        raindrop_option_list.add_options(raindrop_options)

    @on(OptionList.OptionSelected, selector="#collection_option_list")
    async def select_collection(self, event: OptionList.OptionSelected):
        collection_id = event.option.id
        raindrops = await self.database_manager.get_raindrops_by_collection_id(collection_id)
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
