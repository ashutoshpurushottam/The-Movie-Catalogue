# test the database here
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Genre, Base, Movie, User

engine = create_engine('sqlite:///genremoviewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def query_all_users():
    """Retrieve all restaurants from the db and print their info"""
    result = session.query(User).all()
    for user in result:
        print("name: %s\nemail: %s\npicture: %s\nid:%s" %
              (user.name, user.email, user.picture, user.id))
        print("**************************")


def query_all_genres():
    """Retrieve all restaurants from the db and print their info"""
    result = session.query(Genre).all()
    for genre in result:
        print("genre: %s\ndescription: %s\nposter: %s\nuser_id:%s" %
              (genre.name, genre.description, genre.poster, genre.user_id))
        print("**************************")


def query_all_movies():
    """Retrieve all menus and print theif information"""
    result = session.query(Movie).all()
    print("total movies: %s" % len(result))
    for movie in result:
        print("movie poster: %s" % movie.poster)
        print("%s trailer:%s  genre:%s user_id:%s" %
              (movie.name, movie.trailer_url, movie.genre, movie.user_id))
        print("-------------------------------------------------")

#query_all_movies()
query_all_genres()