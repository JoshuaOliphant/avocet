import time
from sqlalchemy.orm import sessionmaker
from models import Collection, Base, Raindrop
from raindrop_api import RaindropAPI
from textual import log

class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine
        # Create a session factory
        self.Session = sessionmaker(bind=engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_collections(self):
        start_time = time.time()
        session = self.Session()
        raindrop_api = RaindropAPI()
        collections = raindrop_api.getCollections()
        for collection_data in collections:
            collection = Collection(id=collection_data['_id'], title=collection_data['title'])
            session.add(collection)
            raindrops = raindrop_api.getRaindropsByCollectionID(collection_data['_id'])
            for raindrop_data in raindrops:
                raindrop = Raindrop(id=raindrop_data['_id'], excerpt=raindrop_data['excerpt'], title=raindrop_data['title'], link=raindrop_data['link'], collection_id=collection.id)
                session.add(raindrop)
        session.commit()
        end_time = time.time()
        log(f"Added in {end_time - start_time} seconds")

    def getCollections(self):
        session = self.Session()
        collections = session.query(Collection).all()
        return collections

    def getRaindropsByCollectionID(self, collection_id):
        session = self.Session()
        raindrops = session.query(Raindrop).filter(Raindrop.collection_id == collection_id).all()
        return raindrops
    
    def getRaindropByRaindropID(self, raindrop_id):
        session = self.Session()
        raindrop = session.query(Raindrop).filter(Raindrop.id == raindrop_id).first()
        return raindrop
    
    def update_collections(self):
        start_time = time.time()
        session = self.Session()
        raindrop_api = RaindropAPI()
        collections = raindrop_api.getCollections()
        existing_collections = self.getCollections()
        not_existing_collections = [Collection(id=collection_data['_id'], title=collection_data['title']) for collection_data in collections if collection_data['_id'] not in [c.id for c in existing_collections]]
        session.add_all(not_existing_collections)
        session.commit()
        for collection_data in collections:
            raindrops = raindrop_api.getRaindropsByCollectionID(collection_data['_id'])
            existing_raindrops = self.getRaindropsByCollectionID(collection_data['_id'])
            not_existing_raindrops = [Raindrop(id=raindrop_data['_id'], excerpt=raindrop_data['excerpt'], title=raindrop_data['title'], link=raindrop_data['link'], collection_id=collection_data['_id']) for raindrop_data in raindrops if raindrop_data['_id'] not in [r.id for r in existing_raindrops]]
            session.add_all(not_existing_raindrops)
            session.commit()
        end_time = time.time()
        log(f"Updated in {end_time - start_time} seconds")
