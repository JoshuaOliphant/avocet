from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import Collection, Base, Raindrop, Update
from textual import log

class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine
        # Create a session factory
        self.Session = sessionmaker(bind=engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_collection(self, collection_data):
        session = self.Session()
        collection = Collection(id=collection_data['_id'],
                                title=collection_data['title'],
                                description=collection_data["description"],
                                count=collection_data['count'],
                                created=datetime.strptime(collection_data['created'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                last_update=datetime.strptime(collection_data['lastUpdate'], "%Y-%m-%dT%H:%M:%S.%fZ"))
        session.add(collection)
        session.commit()

    def add_raindrops(self, raindrop_data_list, collection_id):
        session = self.Session()
        for raindrop_data in raindrop_data_list:
            raindrop = Raindrop(id=raindrop_data['_id'],
                                excerpt=raindrop_data['excerpt'],
                                note=raindrop_data['note'],
                                title=raindrop_data['title'],
                                link=raindrop_data['link'],
                                created=datetime.strptime(raindrop_data['created'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                last_update=datetime.strptime(raindrop_data['lastUpdate'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                collection_id=collection_id,
                                tags=raindrop_data["tags"])
            session.add(raindrop)
        session.commit()

    def add_raindrop(self, raindrop):
        session = self.Session()
        session.add(raindrop)
        session.commit()

    def get_collections(self):
        session = self.Session()
        collections = session.query(Collection).all()
        return collections

    def get_raindrops_by_collection_id(self, collection_id):
        session = self.Session()
        raindrops = session.query(Raindrop).filter(Raindrop.collection_id == collection_id).all()
        return raindrops

    def get_raindrop_by_raindrop_id(self, raindrop_id):
        session = self.Session()
        raindrop = session.query(Raindrop).filter(Raindrop.id == raindrop_id).first()
        return raindrop

    def get_all_raindrops(self):
        session = self.Session()
        return session.query(Raindrop).all()

    def get_all_raindrop_urls(self):
        session = self.Session()
        return session.query(Raindrop).with_entities(Raindrop.link).all()

    def get_updated_raindrops(self, updated_after):
        session = self.Session()
        raindrops = session.query(Raindrop).filter(Raindrop.last_update > updated_after).all()
        return raindrops

    def update_raindrops(self, raindrops):
        session = self.Session()
        session.add_all(raindrops)
        session.commit()

    def update_last_update(self):
        session = self.Session()
        update = session.query(Update).first()
        if not update:
            log("Setting update first time")
            update = Update(last_update=datetime.now())
            session.add(update)
        else:
            log("Updating last_update")
            update.last_update = datetime.now()
            session.add(update)
        log(f"Committing update {update}")
        session.commit()

    def get_last_update(self):
        session = self.Session()
        return session.query(Update).first()
