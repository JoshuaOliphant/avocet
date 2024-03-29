import os
import time
import webbrowser
from textual import on, work, log
from textual.app import App, ComposeResult
from textual.containers import Center, VerticalScroll, Vertical
from textual.widgets import OptionList, ProgressBar, Label, MarkdownViewer, Header, Footer
from textual.widgets.option_list import Option
from sqlalchemy import create_engine
from database_manager import DatabaseManager
from raindrop_api import RaindropAPI
from ai import AI

class Avocet(App):

    CSS_PATH = "avocet.tcss"
    BINDINGS = [
        ("o", "open_link()", "Open in browser")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="progress_bars"):
            yield Label("Loading database...", id="database_label")
            yield ProgressBar(id="database", total=100)
            yield Label("Getting summaries from OpenAI", id="summary_label")
            yield ProgressBar(id="summaries", total=100)
        with Center():
            yield OptionList(id="collection_option_list")
            yield OptionList(id="raindrop_option_list")
        with VerticalScroll():
            yield MarkdownViewer(id='markdown_viewer')
        yield Footer()

    async def on_mount(self) -> None:
        db_name = os.environ.get("DB_NAME", "avocet")
        db_path = f'{db_name}.sqlite'
        is_initialized = True
        if not os.path.exists(db_path):
            is_initialized = False
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.database_manager = DatabaseManager(self.engine)
        self.ai = AI()
        self.startup(is_initialized)

    @work
    async def startup(self, is_initialized):
        start_time = time.time()
        raindrop_api = RaindropAPI()

        if not is_initialized:
            log("Initializing...")
            await self.initialize_db(raindrop_api)
            await self.add_text()
        else:
            log("Updating...")
            await self.update_db(raindrop_api)
            await self.update_text()

        self.database_manager.update_last_update()
        self.query_one("#progress_bars").remove()
        await self.initialize_view()
        end_time = time.time()
        log(f"Startup time: {start_time-end_time}")

    async def initialize_db(self, raindrop_api):
        self.database_manager.create_tables()
        collection_data_list = await raindrop_api.get_collections()
        self.query_one("#database").update(total=len(collection_data_list))
        for collection_data in collection_data_list:
            self.database_manager.add_collection(collection_data)
            raindrop_data_list = await raindrop_api.get_raindrops_by_collection_id(collection_data["_id"])
            self.database_manager.add_raindrops(raindrop_data_list, collection_data["_id"])
            self.query_one("#database").advance(1)

    async def update_db(self, raindrop_api):
        last_update = self.database_manager.get_last_update().last_update
        formatted_date = last_update.strftime("%Y-%m-%d")
        collections = self.database_manager.get_collections()
        self.query_one("#database").update(total=len(collections))
        for collection in collections:
            raindrops = await raindrop_api.get_raindrops_by_collection_id(
                collection.id,
                search=f"lastUpdate:{formatted_date}")
            log(f"Raindrops to update: {raindrops}")
            self.database_manager.add_raindrops(raindrops, collection.id)
            self.query_one("#database").advance(1)

    async def add_text(self):
        raindrops = self.database_manager.get_all_raindrops()
        self.query_one("#summaries").update(total=len(raindrops))
        for raindrop in raindrops:
            markdown = await self.ai.html_to_markdown(raindrop.link)
            log(f"Markdown: {markdown}")
            if markdown:
                raindrop.summary = markdown[0]['article_summary']
            self.query_one("#summaries").advance(1)
        self.database_manager.update_raindrops(raindrops)

    async def update_text(self):
        last_update = self.database_manager.get_last_update()
        updated_raindrops = self.database_manager.get_updated_raindrops(last_update.last_update)
        log(f"Number of raindrops to update: {len(updated_raindrops)}")
        self.query_one("#summaries").update(total=len(updated_raindrops))
        for raindrop in updated_raindrops:
            markdown = await self.ai.html_to_markdown(raindrop.link)
            log(f"Markdown: {markdown}")
            if markdown:
                raindrop.summary = markdown[0]['article_summary']
            self.query_one("#summaries").advance(1)
        self.database_manager.update_raindrops(updated_raindrops)

    async def initialize_view(self):
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
        markdown_viewer = self.query_one("Markdown")
        await markdown_viewer.update(raindrops[0].summary)

    @on(OptionList.OptionSelected, selector="#collection_option_list")
    def select_collection(self, event: OptionList.OptionSelected):
        collection_id = event.option.id
        raindrops = self.database_manager.get_raindrops_by_collection_id(collection_id)
        options = [Option(prompt=raindrop.title, id=raindrop.id) for raindrop in raindrops]
        option_list = self.query_one("#raindrop_option_list")
        option_list.clear_options()
        option_list.add_options(options)

    @on(OptionList.OptionHighlighted, selector="#raindrop_option_list")
    async def highlight_raindrop(self, event: OptionList.OptionHighlighted):
        raindrop_id = event.option.id
        raindrop = self.database_manager.get_raindrop_by_raindrop_id(raindrop_id)
        markdown = self.query_one("Markdown")
        await markdown.update(raindrop.summary)

    @on(OptionList.OptionSelected, selector="#raindrop_option_list")
    async def select_raindrop(self, event: OptionList.OptionSelected):
        raindrop_id = event.option.id
        raindrop = self.database_manager.get_raindrop_by_raindrop_id(raindrop_id)
        webbrowser.open(raindrop.link)


if __name__ == "__main__":
    avocet = Avocet()
    avocet.run()
