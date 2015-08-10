import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    def itemsInCategory():
        return


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    create_At = Column(DateTime, default=func.now())
    edited_At = Column(DateTime, onupdate=func.now())
    name = Column(String(50), nullable=False)
    price = Column(String(8))
    description = Column(String(300), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        #Return objects data in easily serialize format
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id
        }


engine = create_engine('sqlite:///categoryproject.db')

Base.metadata.create_all(engine)
