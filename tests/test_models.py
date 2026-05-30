# ABOUTME: Tests for the SQLAlchemy declarative models.
# ABOUTME: Verifies table creation and the Raindrop.summary nullable column.
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from avocet.models import Base, Collection, Raindrop, Setting


def test_tables_create():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    names = set(inspect(engine).get_table_names())
    assert {"collections", "raindrops", "settings"} <= names


def test_raindrop_summary_is_nullable():
    summary_col = Raindrop.__table__.c.summary
    assert summary_col.nullable is True


def test_collection_has_parent_id_column():
    # parent_id is new in the 2.0 models (the old schema lacked it); this asserts
    # the nested-collection support the data layer depends on.
    assert "parent_id" in Collection.__table__.c
    assert Collection.__table__.c.parent_id.nullable is True


def test_setting_key_is_primary_key():
    assert Setting.__table__.c.key.primary_key is True
