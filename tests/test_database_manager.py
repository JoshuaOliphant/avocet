import pytest
from pytest_mock import MockerFixture

from avocet.database_manager import DatabaseManager
from avocet.models import Raindrop

@pytest.fixture
def db(mocker: MockerFixture):
    mock_engine = mocker.MagicMock()
    return DatabaseManager(mock_engine)

def test_add_collection(db):
    """
    This function is used to test the 'add_collection' method of the 'db' object.

    Parameters:
        db (object): The database object that contains the 'add_collection' method.

    Returns:
        None
    """
    # Call with sample data
    collection_data = {
        "_id": "1",
        "title": "Test Collection",
        "description": "Sample collection for testing",
    }
    db.add_collection(collection_data)

    # Validate collection added
    collections = db.get_collections()
    assert len(collections) == 1
    assert collections[0].id == "1"
    assert collections[0].title == "Test Collection"

def test_add_raindrops(db):
    # Add sample collection
    db.add_collection({
        "_id": "1",
        "title": "Test Collection"
    })

    # Call with sample raindrops data
    raindrops_data = [
        {
            "_id": "1",
            "title": "Test Raindrop 1",
        },
        {
            "_id": "2", 
            "title": "Test Raindrop 2",
        }
    ]
    db.add_raindrops(raindrops_data, "1")

    # Validate raindrops added for collection
    raindrops = db.get_raindrops_by_collection_id("1")
    assert len(raindrops) == 2
    assert raindrops[0].id == "1"
    assert raindrops[1].id == "2"

def test_get_collections(db):
    # Call
    collections = db.get_collections()
    
    # Validate collections returned
    assert isinstance(collections, list)

def test_get_raindrops_by_collection_id(db):
    # Add sample collection and raindrops
    db.add_collection({
        "_id": "1", 
        "title": "Test Collection"
    })
    db.add_raindrops([{"_id": "1"}], "1")
    
    # Call 
    raindrops = db.get_raindrops_by_collection_id("1")

    # Validate raindrops for collection returned
    assert len(raindrops) == 1
    assert raindrops[0].id == "1"

def test_get_raindrop_by_raindrop_id(db):
    # Add sample raindrop
    db.add_raindrop(Raindrop(id="1"))
    
    # Call
    raindrop = db.get_raindrop_by_raindrop_id("1")

    # Validate specific raindrop returned
    assert raindrop.id == "1"