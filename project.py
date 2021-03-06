import os
import sys
import httplib2
import random
import string
import json
import requests
import re

from functools import wraps, update_wrapper
from datetime import datetime
from database_setup import Genre, Base, Movie, User

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask import session as login_session
from flask import make_response
from flask import abort
from werkzeug import secure_filename
# CSRF protection
from flask.ext.seasurf import SeaSurf

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import IntegrityError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


# Configuration for picture uploads
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FILESIZE_LIMIT = 4 * 1024 * 1024  # Max Size: 4 MB


# app and extension
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = UPLOAD_FILESIZE_LIMIT
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
csrf = SeaSurf(app)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///genremoviewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
Session = scoped_session(DBSession)
session = DBSession()


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        """
        prevents caching of client browser
        decorator to be used where controlling flash messages is required
        Input: View
        Returns: wrapper over the view for cache control
        """
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers[
            'Cache-Control'] = 'no-store, no-cache, must-revalidate,\
             post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def login_required(func):
    """
    Function decorator that controls user permissions.
    Prevents non-logged in users from performing CRUD operations
    Input: func: The function to decorate.
    Return: decorated function with added permission controls.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            flash('Please log in first to manage movies lists.')
            return redirect('/')
        return func(*args, **kwargs)
    return decorated_function


# home page
@app.route('/')
@app.route('/genres/')
@nocache
def show_genres():
    """Show all genres and lists"""
    # genres in a random order
    genres = session.query(Genre).order_by(func.random()).all()
    user = None
    # retrieve user from email in login_session
    if 'email' in login_session:
        user = get_user(login_session['email'])
    return render_template('genres.html', genres=genres, user=user)

# page for showing movies of a genre or a list


@app.route('/genre/<int:genre_id>/movies/')
@app.route('/genre/<int:genre_id>/')
@nocache
def show_movies_genre(genre_id):
    """show all movies from a genre"""
    user = get_user_from_session(login_session)
    # retrieve movies and genre
    movies = session.query(Movie).filter_by(
        genre_id=genre_id).order_by(func.random()).all()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    return render_template('genre_movies.html',
                           movies=movies,
                           genre=genre,
                           user=user)

# page for creating a new genre


@app.route('/genre/<int:user_id>/new/', methods=['GET', 'POST'])
@login_required
def create_new_genre(user_id):
    """create a new genre"""
    user = get_user_from_session(login_session)
    if request.method == 'POST':
        new_genre = Genre(name=request.form["name"],
                          description=request.form["description"],
                          user_id=user_id)
        # handling picture upload for the genre
        pic_file = request.files['poster']
        if pic_file and permitted_file(pic_file.filename):
            filename = secure_filename(pic_file.filename)
            # renaming pic file name to avoid any collision
            filename = strip_string(
                new_genre.name) +\
                filename.split(".")[0] + "-genre." + filename.split(".")[1]
            # save the file to the img folder
            pic_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_genre.poster = filename

        session.add(new_genre)
        session.commit()
        flash("A new list '%s' is created by %s." %
              (new_genre.name, user.name))
        return redirect('/')
    else:
        return render_template('create_genre.html', user=user)

# edit genre page


@app.route('/genre/<int:genre_id>/<int:user_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def edit_genre(genre_id, user_id):
    """edit genre details"""
    user = get_user_from_session(login_session)
    genre = session.query(Genre).filter_by(id=genre_id).one()

    # only genre creator can edit its description
    if user and user.id == genre.user_id:
        if request.method == 'POST':
            genre.name = request.form["name"]
            genre.description = request.form["description"]

            # handling picture upload for the genre
            pic_file = request.files['poster']

            if pic_file and permitted_file(pic_file.filename):
                filename = secure_filename(pic_file.filename)
                # rename file to prevent collision
                filename = strip_string(
                    genre.name) + filename.split(".")[0] +\
                    "-genre." + filename.split(".")[1]
                pic_file.save(os.path.join(
                    app.config['UPLOAD_FOLDER'], filename))
                # remove older poster
                if genre.poster:
                    path = "%s/%s" % (app.config['UPLOAD_FOLDER'],
                                      genre.poster)
                    os.remove(path)
                # update poster
                genre.poster = filename

            session.add(genre)
            session.commit()
            flash("The list '%s' has been edited" % genre.name)
            return redirect('/')
        else:
            return render_template("edit_genre.html", user=user, genre=genre)
    else:
        # user is not matching with the genre creator
        abort(401)

# delete genre page


@app.route('/genre/<int:genre_id>/<int:user_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def delete_genre(genre_id, user_id):
    """delete genre alongwith associated movies"""
    user = get_user_from_session(login_session)
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if user and user.id == genre.user_id:
        if request.method == 'POST':
            # get all movies of the genre
            movies = session.query(Movie).filter_by(genre_id=genre_id).all()
            for movie in movies:
                session.delete(movie)
                # remove posters of movies
                if movie.poster:
                    path = "%s/%s" % (app.config['UPLOAD_FOLDER'],
                                      movie.poster)
                    try:
                        os.remove(path)
                    except e:
                        app.logger.error(
                            "Exception trying to removing movie poster: %s", (e))
            # delete poster of the genre
            if genre.poster:
                path = "%s/%s" % (app.config['UPLOAD_FOLDER'], genre.poster)
                try:
                    os.remove(path)
                except e:
                    app.logger.error(
                        "Can not delete poster of the genre: %s", (e))

            session.delete(genre)
            session.commit()
            flash("The list '%s' has been deleted." % genre.name)
            return redirect('/')
        else:
            return render_template("delete_genre.html", user=user, genre=genre)
    else:
        abort(401)

# add a movie page


@app.route('/genre/<int:genre_id>/<int:user_id>/new/', methods=['GET', 'POST'])
@login_required
def create_movie(genre_id, user_id):
    """create a new movie"""
    user = get_user_from_session(login_session)
    # retrieve genre
    genre = session.query(Genre).filter_by(id=genre_id).one()
    # accept post only if user is not None and user id matches with the genre
    if user and user.id == genre.user_id:
        if request.method == 'POST':
            new_movie = Movie(name=request.form["name"],
                              storyline=request.form["storyline"],
                              trailer_url=request.form["trailer_url"],
                              user_id=user_id,
                              genre_id=genre_id)
            # handling picture upload for the genre
            pic_file = request.files['poster']

            if pic_file and permitted_file(pic_file.filename):
                filename = secure_filename(pic_file.filename)
                # rename pic to prevent collision
                filename = strip_string(
                    genre.name + new_movie.name) +\
                    filename.split(".")[0] + "-movie." + filename.split(".")[1]
                pic_file.save(os.path.join(
                    app.config['UPLOAD_FOLDER'], filename))
                new_movie.poster = filename

            session.add(new_movie)
            session.commit()
            flash("A new movie '%s' has been added." % new_movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id))
        else:
            return render_template("create_movie.html", genre=genre, user=user)
    else:
        abort(401)

# edit movie page


@app.route('/genre/<int:genre_id>/<int:movie_id>/edit_movie',
           methods=['GET', 'POST'])
@login_required
def edit_movie(genre_id, movie_id):
    """edit movie detail"""
    user = get_user_from_session(login_session)
    try:
        movie = session.query(Movie).filter_by(id=movie_id).one()
        genre = session.query(Genre).filter_by(id=genre_id).one()
    except:
        return redirect('/')
    if user and user.id == movie.user_id:
        if request.method == 'POST':
            movie.name = request.form["name"]
            movie.storyline = request.form["storyline"]
            movie.trailer_url = request.form["trailer_url"]

            # handling picture upload for the movie
            pic_file = request.files['poster']

            if pic_file and permitted_file(pic_file.filename):
                filename = secure_filename(pic_file.filename)
                filename = strip_string(
                    genre.name + movie.name) +\
                    filename.split(".")[0] + "-movie." + filename.split(".")[1]
                pic_file.save(os.path.join(
                    app.config['UPLOAD_FOLDER'], filename))
                # remove older poster
                if movie.poster:
                    path = "%s/%s" % (app.config['UPLOAD_FOLDER'],
                                      movie.poster)
                    try:
                        os.remove(path)
                    except e:
                        app.logger.error(
                            "Exception in trying to remove movie poster %s",
                            (e))
                # update poster
                movie.poster = filename

            session.add(movie)
            session.commit()
            flash("The movie '%s' has been edited" % movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id))
        else:
            return render_template("edit_movie.html", movie=movie, user=user)
    else:
        abort(401)

# show movie details


@app.route('/genre/<int:genre_id>/<int:movie_id>/')
def show_movie_details(genre_id, movie_id):
    """show movie details"""
    user = get_user_from_session(login_session)
    movie = session.query(Movie).filter_by(id=movie_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    youtube_url = ""
    if movie.trailer_url.startswith("https://youtu.be/"):
        append = movie.trailer_url.split(".be/")[1]
        youtube_url = "https://www.youtube.com/embed/" + append
    elif movie.trailer_url.startswith("https://www.youtube.com/watch?v="):
        append = movie.trailer_url.split("?v=")[1]
        youtube_url = "https://www.youtube.com/embed/" + append
    return render_template("movie_details.html",
                           movie=movie,
                           url=youtube_url,
                           user=user,
                           genre_id=genre_id)


# delete movie page
@app.route('/genre/<int:genre_id>/<int:movie_id>/delete_movie',
           methods=['GET', 'POST'])
@login_required
def delete_movie(genre_id, movie_id):
    """
    edit movie info
    """
    user = get_user_from_session(login_session)
    # retrieve movie and genre
    try:
        movie = session.query(Movie).filter_by(id=movie_id).one()
        genre = session.query(Genre).filter_by(id=genre_id).one()
    except:
        return redirect('/')
    if user and user.id == movie.user_id:
        if request.method == 'POST':
            # remove old movie poster
            if movie.poster:
                path = "%s/%s" % (app.config['UPLOAD_FOLDER'], movie.poster)
                app.logger.error("Path: %s", (path))
                try:
                    os.remove(path)
                except e:
                    app.logger.error(
                        "Exception trying to removie movie poster: %s", (e))
            session.delete(movie)
            session.commit()
            flash("The movie '%s' has been deleted" % movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id))
        else:
            return render_template("delete_movie.html", movie=movie, user=user)
    else:
        abort(401)


@app.errorhandler(413)
def upload_size_error(e):
    """Catches 413 error from photo size upload"""
    user = get_user_from_session(login_session)
    return render_template('413.html', user=user), 413


@app.errorhandler(401)
def unauthorized_error(e):
    """Catches 401 error from unauthorized success"""
    user = get_user_from_session(login_session)
    return render_template('401.html', user=user), 413


@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error("Unhandled exception %s", (e))
    if isinstance(e, IntegrityError):
        error = "Duplicate Entry Tried."
    else:
        error = "Some server error occured."
    session.rollback()
    Session.remove()
    return render_template('unhandled.html', error=error), 500


# login page
@app.route('/login/')
def show_login():
    # anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Google connect
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    print("user data:", data)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists or not, if not create a new one
    user = get_user(login_session['email'])
    if not user:
        user_id = create_user(login_session)
        user = get_user_from_id(user_id)
    login_session['user_id'] = user.id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: 100px;\
    -webkit-border-radius: 100px;-moz-border-radius: 100px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Disconnect google
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    login_session['access_token'] = access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def disconnect():
    """ Handles the disconnection of all accounts """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        return redirect('/')
    else:
        return redirect('/')


@app.route('/json')
@app.route('/movies/json')
def index_json():
    """Route for JSON endpoint. Return all the movies"""
    genres = session.query(Genre).all()
    movies = []
    for genre in genres:
        movies.append(genre.serializable)
        items = session.query(Movie).filter_by(genre_id=genre.id).all()
        movies[-1]['movies'] = [i.serializable for i in items]
    return jsonify(Lists=movies)


@app.route('/json/movie/<int:movie_id>')
@app.route('/movies/json/movie/<int:movie_id>')
def index_json_movie(movie_id):
    """Route for JSON endpoint. Return a movie info for id"""
    movie = session.query(Movie).filter_by(id=movie_id).one()
    return jsonify(Movie=movie.serializable)

@app.route('/json/genre/<int:genre_id>')
@app.route('/json/movies/genre/<int:genre_id>')
def index_json_genre(genre_id):
    """Route for JSON endpoint. Return movies of a genre"""
    genre = session.query(Genre).filter_by(id=genre_id).one()
    movies = session.query(Movie).filter_by(genre_id=genre_id).all()
    lst = []
    lst.append(genre.serializable)
    lst[-1]['movies'] = [i.serializable for i in movies]
    return jsonify(Movies=lst)


def strip_string(s):
    """
    strips all non-alphanumeric characters form a string
    and returns the remaining string
    """
    pattern = re.compile('\W')
    stripped = re.sub(pattern, '', s)
    return stripped


def permitted_file(filename):
    """Checks format of an uploaded file"""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def create_user(login_session):
    """Creates a new user and save in db.Returns its id."""
    new_user = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    return new_user.id


def get_user(email):
    """Gets user by its email. If the email does not match returns None."""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None


def get_user_from_session(s):
    """Returns user from the login_sessino"""
    user = None
    if 'email' in s:
        email = s['email']
        user = get_user(email)
    return user


def get_user_from_id(id):
    """Gets user from id. In case of no match returns None."""
    try:
        user = session.query(User).filter_by(id=id).one()
        return user
    except:
        return None


def get_user_id(email):
    """Gets user id associated with the input email"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
