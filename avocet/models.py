from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    count = Column(Integer)
    created = Column(DateTime)
    last_update = Column(DateTime)
    raindrops = relationship("Raindrop", backref=backref("collection"))

class Raindrop(Base):
    __tablename__ = 'raindrops'
    id = Column(Integer, primary_key=True)
    excerpt = Column(String)
    note = Column(String)
    title = Column(String)
    link = Column(String)
    created = Column(DateTime)
    last_update = Column(DateTime)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    tags = Column(JSON)
    # non-raindrop columns
    summary = Column(String)

class Update(Base):
    __tablename__ = "update"
    id = Column(Integer, primary_key=True)
    last_update = Column(DateTime)
