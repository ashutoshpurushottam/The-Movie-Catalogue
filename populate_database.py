"""
Code to automatically upload some genres/lists and movies to the database. 
The posters are not fetched as the project exceeded expectations requires
image CRUD operations.
"""

import requests
import tmdbsimple as tmdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Genre, Base, Movie, User

# Get request token from the moviedb
from secret import api_key as API_KEY
tmdb.API_KEY = API_KEY
BASE_URL_SECURE_STRING = "https://api.themoviedb.org/3/"
GET_TOKEN_METHOD = "authentication/token/new"
LOGIN_METHOD = "authentication/token/validate_with_login"
GET_SESSION_ID_METHOD = "authentication/session/new"
GET_ACCOUNT_INFO_METHOD = "account"
# URLs for trailer and posters for movie objects
YOUTUBE_BASE_URL = 'https://youtu.be/'
TMDB_POSTER_BASE_URL = 'http://image.tmdb.org/t/p/w500/'
from secret import username as USERNAME
from secret import password as PASSWORD

# Bind engine to the metadata of base class.
engine = create_engine('sqlite:///genremoviewithusers.db')
Base.metadata.bind = engine

# Session object as staging zone for CRUD operations on DB.
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add User
user = User(
    name="Ashutosh Purushottam",
    email="sonu.puru1807@gmail.com",
    picture="https://lh4.googleusercontent.com/-in2C7dQwUEQ/AAAAAAAAAAI/AAAAAAAADEU/-YXW7m2A1uo/photo.jpg"
)
session.add(user)
session.commit()

# Add genres
action = Genre(
    name="action",
    description="A film genre in which the protagonist or protagonists end up in a series of challenges that"
    "typically include violence, close combat, physical feats and frantic chases",
    user_id=1)

session.add(action)
session.commit()

romance = Genre(
    name="romance",
    description="A film genre that focus on passion, emotion, and the affectionate romantic involvement of the"
    " main characters and the journey that their genuinely strong, true and pure romantic love takes them"
    " through dating, courtship or marriage.",
    user_id=1)

session.add(romance)
session.commit()

animation = Genre(
    name="animation",
    description="Animated Films are ones in which individual drawings, paintings, or illustrations are"
    " photographed frame by frame (stop-frame cinematography). Usually, each frame differs slightly from"
    " the one preceding it, giving the illusion of movement when frames are projected in rapid succession"
    " at 24 frames per second.",
    user_id=1)

session.add(animation)
session.commit()

comedy = Genre(
    name="comedy",
    description="Comedy is a genre of film in which the main emphasis is on humour. These films are designed"
    " to make the audience laugh through amusement and most often work by exaggerating characteristics for"
    " humorous effect.",
    user_id=1)

session.add(comedy)
session.commit()

horror = Genre(
    name="horror",
    description="Horror Films are unsettling films designed to frighten and panic, cause dread and alarm,"
    " and to invoke our hidden worst fears, often in a terrifying, shocking finale, while captivating and"
    " entertaining us at the same time in a cathartic experience.",
    user_id=1)

session.add(horror)
session.commit()

fantasy = Genre(
    name="fantasy",
    description="Fantasy films are films that belong to the fantasy genre with fantastic themes, usually"
    " involving magic, supernatural events, mythology, folklore, or exotic fantasy worlds.",
    user_id=1)

session.add(fantasy)
session.commit()


def get_request_token():
    """
    gets request token for the user
    """
    url_string = BASE_URL_SECURE_STRING + GET_TOKEN_METHOD + "?api_key=" + API_KEY
    r = requests.get(url_string)
    config = r.json()
    token = config['request_token']
    return token


def authenticate_token():
    """
    authenticate token
    """
    token = get_request_token()
    parameters = "?api_key=" + API_KEY + "&request_token=" + \
        token + "&username=" + USERNAME + "&password=" + PASSWORD
    url_string = BASE_URL_SECURE_STRING + LOGIN_METHOD + parameters
    r = requests.get(url_string)
    return token


def get_session_id():
    """
    get session id for user
    """
    token = authenticate_token()
    parameters = "?api_key=" + API_KEY + "&request_token=" + token
    url_string = BASE_URL_SECURE_STRING + GET_SESSION_ID_METHOD + parameters
    r = requests.get(url_string)
    response_json = r.json()
    session_id = response_json['session_id']
    return session_id, token


def get_account_id():
    """
    gets account id for the user
    """
    session_id, token = get_session_id()
    parameters = "?api_key=" + API_KEY + "&session_id=" + session_id
    url_string = BASE_URL_SECURE_STRING + GET_ACCOUNT_INFO_METHOD + parameters
    r = requests.get(url_string)
    response_json = r.json()
    user_id = response_json['id']
    return user_id, session_id


def get_favorite_movies_id():
    """
    returns list of ids of movies in the favorite list of the user
    """
    user_id, session_id = get_account_id()
    get_favorite_movies_method = "account/{id}/favorite/movies"
    get_favorite_movies_method = get_favorite_movies_method.format(id=user_id)
    movies_array = []
    for count in range(1, 3):
        parameters = "?api_key=%s&session_id=%s&sort_by=created_at.asc&page=%s" % (
            API_KEY, session_id, count)
        url_string = BASE_URL_SECURE_STRING + get_favorite_movies_method + parameters
        r = requests.get(url_string)
        response_json = r.json()
        movies_array += response_json['results']

    return [movie['id'] for movie in movies_array]


count = 1
for id in get_favorite_movies_id():
    # get movie title
    movie_trailer_url = ""
    movie_videos = tmdb.Movies(id).videos()
    if movie_videos['results'] and len(movie_videos['results']) > 0:
        trailer_video = movie_videos['results'][0]
        movie_trailer_url = YOUTUBE_BASE_URL + trailer_video['key']
        print("Movie trailer:", movie_trailer_url)
    # get title, overview, poster
    movie_info = tmdb.Movies(id).info()
    movie_title = movie_info['title']
    movie_overview = movie_info['overview']
    movie_poster_url = TMDB_POSTER_BASE_URL + movie_info['poster_path']

    if count <= 5:
        movie_genre = action
    elif count <= 10:
        movie_genre = romance
    elif count <= 15:
        movie_genre = animation
    elif count <= 20:
        movie_genre = comedy
    elif count <= 25:
        movie_genre = horror
    else:
        movie_genre = fantasy

    movie = Movie(
        name=movie_title,
        storyline=movie_overview,
        trailer_url=movie_trailer_url,
        genre=movie_genre,
        user_id=1
    )

    session.add(movie)
    session.commit()
    count += 1
