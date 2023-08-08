import os
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from sqlalchemy import create_engine
from database_manager import DatabaseManager

class Avocet(App):

    def compose(self) -> ComposeResult:
        yield OptionList(id="collection_option_list", )
        yield OptionList(id="raindrop_option_list")

    def on_mount(self) -> None:
        self.initialize_collections()
        self.initialize_raindrops(self.collections[0].id)
        
    

    def initialize_collections(self):
        # Check if the database exists
        if not os.path.exists("avocet.db"):
            # Create the database
            self.database_manager.create_tables()
            # Add the collections to the database
            self.database_manager.add_collections()
        self.engine = create_engine('sqlite:///avocet.db')
        self.database_manager = DatabaseManager(self.engine)
        self.collections = self.database_manager.getCollections()
        options = [Option(prompt=collection.title, id=collection.id) for collection in self.collections]
        option_list = self.query_one("#collection_option_list")
        option_list.add_options(options)

    def initialize_raindrops(self, collection_id=None):
        self.raindrops = self.database_manager.getRaindropsByCollectionID(collection_id)
        options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in self.raindrops]
        option_list = self.query_one("#raindrop_option_list")
        option_list.add_options(options)
 
    @on(OptionList.OptionSelected, selector="#collection_option_list")
    def select_collection(self, event: OptionList.OptionSelected):
        collection_id = event.option.id
        raindrops = self.database_manager.getRaindropsByCollectionID(collection_id)
        options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in raindrops]
        option_list = self.query_one("#raindrop_option_list")
        option_list.clear_options()
        option_list.add_options(options)


if __name__ == "__main__":
    avocet = Avocet()
    avocet.run()
