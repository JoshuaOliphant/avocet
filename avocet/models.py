from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    count = Column(Integer)
    last_action = Column(DateTime)
    created = Column(DateTime)
    last_update = Column(DateTime)
    raindrops = relationship("Raindrop", backref=backref("collection"))

class Raindrop(Base):
    __tablename__ = 'raindrops'
    id = Column(Integer, primary_key=True)
    excerpt = Column(String)
    note = Column(String)
    type = Column(String)
    title = Column(String)
    link = Column(String)
    created = Column(DateTime)
    last_update = Column(DateTime)
    domain = Column(String)
    collection_id = Column(Integer, ForeignKey('collections.id'))
