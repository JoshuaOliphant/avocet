import os
from textual.app import App, ComposeResult
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from sqlalchemy import create_engine
from database_manager import DatabaseManager

class Avocet(App):
    def compose(self) -> ComposeResult:
        yield OptionList(id="option_list")

    def on_mount(self) -> None:
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
        option_list = self.query_one("#option_list")
        option_list.add_options(options)


if __name__ == "__main__":
    avocet = Avocet()
    avocet.run()
