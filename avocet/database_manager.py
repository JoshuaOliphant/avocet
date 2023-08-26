from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import Collection, Base, Raindrop
from raindrop_api import RaindropAPI

class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine
        # Create a session factory
        self.Session = sessionmaker(bind=engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    async def add_collections(self):
        session = self.Session()
        raindrop_api = RaindropAPI()

        collection_data_list = await raindrop_api.get_collections()
        for collection_data in collection_data_list:
            collection = Collection(id=collection_data['_id'],
                                    title=collection_data['title'],
                                    description=collection_data["description"],
                                    count=collection_data['count'],
                                    created=datetime.strptime(collection_data['created'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                    last_update=datetime.strptime(collection_data['lastUpdate'], "%Y-%m-%dT%H:%M:%S.%fZ"))
            session.add(collection)
            await self.add_raindrops(collection_data=collection, session=session, raindrop_api=raindrop_api)
        session.commit()

    async def add_raindrops(self, collection_data, session, raindrop_api):
        raindrop_data_list = await raindrop_api.get_raindrops_by_collection_id(collection_data.id)
        for raindrop_data in raindrop_data_list:
            raindrop = Raindrop(id=raindrop_data['_id'],
                                excerpt=raindrop_data['excerpt'],
                                note=raindrop_data['note'],
                                title=raindrop_data['title'],
                                link=raindrop_data['link'],
                                created=datetime.strptime(raindrop_data['created'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                last_update=datetime.strptime(raindrop_data['lastUpdate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                collection_id=collection_data.id)
            session.add(raindrop)

    async def get_collections(self):
        session = self.Session()
        collections = session.query(Collection).all()
        return collections

    async def get_raindrops_by_collection_id(self, collection_id):
        session = self.Session()
        raindrops = session.query(Raindrop).filter(Raindrop.collection_id == collection_id).all()
        return raindrops

    def get_raindrop_by_raindrop_id(self, raindrop_id):
        session = self.Session()
        raindrop = session.query(Raindrop).filter(Raindrop.id == raindrop_id).first()
        return raindrop
