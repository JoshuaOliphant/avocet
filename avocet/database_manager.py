from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import Collection, Base, Raindrop
from rich import print as print
from raindrop_api import RaindropAPI

class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine
        # Create a session factory
        self.Session = sessionmaker(bind=engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_collections(self):
        # Create a Raindrop object
        session = self.Session()
        raindrop_api = RaindropAPI()
        collections = raindrop_api.getCollections()
        print(f"collections: {collections}")

        # Iterate over the items and create a Collection object for each item
        for item in collections:
            # Convert last_action, created and last_update to datetime objects
            last_action = datetime.strptime(item['lastAction'], '%Y-%m-%dT%H:%M:%S.%fZ')
            created = datetime.strptime(item['created'], '%Y-%m-%dT%H:%M:%S.%fZ')
            last_update = datetime.strptime(item['lastUpdate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Check if a record with the same id already exists in the database
            existing_collection = session.query(Collection).filter(Collection.id == item['_id']).first()
            if existing_collection:
                # If a record with the same id exists, skip creating the object
                collection = existing_collection
            else:
                # If a record with the same id doesn't exist, create the object
                collection = Collection(id=item['_id'], title=item['title'], description=item['description'], count=item['count'], last_action=last_action, created=created, last_update=last_update)
                # Add the Collection object to the session
                session.add(collection)

            raindrops = raindrop_api.getRaindropsByCollectionID(collection.id)
            for raindrop in raindrops:
                # Convert created and last_update to datetime objects
                created = datetime.strptime(raindrop['created'], '%Y-%m-%dT%H:%M:%S.%fZ')
                last_update = datetime.strptime(raindrop['lastUpdate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                # Check if a record with the same id already exists in the database
                existing_raindrop = session.query(Raindrop).filter(Raindrop.id == raindrop['_id']).first()
                if existing_raindrop:
                    # If a record with the same id exists, skip creating the object
                    raindrop = existing_raindrop
                else:
                    # If a record with the same id doesn't exist, create the object
                    raindrop = Raindrop(id=raindrop['_id'], excerpt=raindrop['excerpt'], note=raindrop['excerpt'], type=raindrop['type'], title=raindrop['title'], link=raindrop['link'], created=created, last_update=last_update, domain=raindrop['domain'], collection_id=collection.id)
                    # Add the Raindrop object to the session
                    session.add(raindrop)

                print(f"Raindrop: {raindrop.title}")
                # Add the Raindrop object to the Collection object
                collection.raindrops.append(raindrop)
                # Add the Raindrop object to the session
                session.add(raindrop)

            print(f"Collection: {collection.title}")
            session.add(collection)

        # Commit the changes to the database
        session.commit()

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
