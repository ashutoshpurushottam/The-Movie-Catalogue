import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    """Users of the movie catalogue"""
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    
class Genre(Base):
    """Genres of movies like comedy, horror etc."""
    __tablename__ = 'genre'
    
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False, unique = True)
    description = Column(String(500), nullable = False)
    poster = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    
    @property
    def serializable(self):
        """Returns object in serializable format"""
        return {
            "name": self.name,
            "description": self.description,
            "poster": self.poster,
            "owner": self.user.name,
            "owner_id": self.user_id,
            "id": self.id,
        }

class Movie(Base):
    """Movie items belonging to different genres"""
    __tablename__ = 'movie'
    
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    storyline = Column(String(500))
    poster = Column(String(250))
    trailer_url = Column(String(250))
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    
    @property
    def serializable(self):
        """Returns object in serializable format"""
        return {
            "name": self.name,
            "storyline": self.storyline,
            "poster": self.poster,
            "trailer_url": self.trailer_url,
            "id": self.id
        }

engine = create_engine('sqlite:///genremoviewithusers.db')
Base.metadata.create_all(engine)


