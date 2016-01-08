import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()

class User(Base):
    """User class used for local permission
    It contains attribute:
    1.name
    2.id
    3.email
    4.picture
    """
    __tablename__ = 'user'
    
    id = Column(Integer,primary_key=True)
    name = Column(String(250),nullable=False)
    email = Column(String(250),nullable=False)
    picture = Column(String(500),nullable=True)

class Coffee (Base):
    """Coffee class contains attribute:
    1.name
    2.id
    3.user_id
    """    
    __tablename__ = 'coffee'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
    #Return object data in easily serializeable format
       return {
        'name' : self.name,
        'id'   : self.id,
        'user_id' : self.user_id,
       }

class MenuItem(Base):
    """MenuItem class used to describe each menu
    It contains attributes:
    1.name
    2.id
    3.description
    4.price
    5.category
    6.coffee_id
    7.user_id
    Note: coffee_id is used to associated with coffee shop.
    user_id is used to associated with user who has ownship.
    """
    __tablename__ = 'menu_item'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(String(8))
    category = Column(String(500))
    coffee_id = Column(Integer,ForeignKey('coffee.id'))
    coffee = relationship(Coffee)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
    #Return object data in easily serializeable format.
        return {
            'name': self.name,
            'id':self.id,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'coffee_id' : self.coffee_id,
            'user_id': self.user_id,
        }


engine = create_engine('sqlite:///coffeeMenu.db')
Base.metadata.create_all(engine)
