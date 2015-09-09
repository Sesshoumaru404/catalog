import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy import func, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    name = Column(String(110), nullable=False)
    admin = Column(Boolean, default=False)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    @property
    def serialize(self):
        # Return object data in easily serializeable format
        return {'name': self.name}

    @property
    def itemsInCategory(self):
        # Return item count per category
        return len(self.items)


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    create_At = Column(DateTime, default=func.now())
    edited_At = Column(DateTime, default=func.now(), onupdate=func.now())
    name = Column(String(50), nullable=False)
    price = Column(Float, default=0.00)
    description = Column(String(300), nullable=False)
    image = Column(String())
    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    category = relationship('Category', backref=backref('items'))
    user = relationship(User)

    @property
    def serialize(self):
        # Return objects data in easily serialize format
        return {
            'name': self.name,
            'description': self.description,
            'create_At': self.create_At,
            'category_name': self.category.name
        }


engine = create_engine(os.getenv("DATABASE_URL"))

Base.metadata.create_all(engine)
