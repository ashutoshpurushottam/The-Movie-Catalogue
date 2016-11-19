import sys
import httplib2
import random, string
import json
import requests

from functools import wraps, update_wrapper
from datetime import datetime
from database_setup import Genre, Base, Movie, User

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask import make_response
from flask import abort
from flask.ext.seasurf import SeaSurf

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


# Configuration for picture uploads
UPLOAD_FOLDER = '/vagrant/the-movie-catalogue/static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FILESIZE_LIMIT = 4 * 1024 * 1024 


# app and extension
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = UPLOAD_FILESIZE_LIMIT
csrf = SeaSurf(app)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///genremoviewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        """
        prevents caching of client browser
        decorator to be used where controlling flash messages is required 
        """
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        
    return update_wrapper(no_cache, view)

def login_required(func):
    """
    Function decorator that controls user permissions.
    Prevents non-logged in users from performing CRUD operations
    Input: func: The function to decorate.
    Returns: decorated function with added permission controls.
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
    # retrieve user from email in login session
    if 'email' in login_session:
        user = get_user(login_session['email'])
    return render_template('genres.html', genres=genres, user=user)

# page for showing movies of a genre or a list
@app.route('/genre/<int:genre_id>/movies/')
@app.route('/genre/<int:genre_id>/')
@nocache
def show_movies_genre(genre_id):
    """show all movies from a genre"""
    user = None
    if 'email' in login_session:
        email = login_session['email']
        user = get_user(email)
    # retrieve movies and genre 
    movies = session.query(Movie).filter_by(genre_id = genre_id).order_by(func.random()).all()
    genre = session.query(Genre).filter_by(id = genre_id).one()
    return render_template('genre_movies.html', movies = movies, genre = genre, user=user)

@app.route('/genre/<int:user_id>/new/', methods=['GET', 'POST'])
@login_required
def create_new_genre(user_id):
    """
    create a new genre
    """
    user = None
    if 'email' in login_session:
        user = get_user(login_session['email'])
    if request.method == 'POST':
        new_genre = Genre(name=request.form["name"], 
            description=request.form["description"],
            poster_url=request.form["poster_url"],
            user_id=user_id)
        session.add(new_genre)
        session.commit()
        flash("A new list %s is created by %s." %(new_genre.name, user.name))
        return redirect('/')
    else:
        return render_template('create_genre.html', user=user)

# edit genre page
@app.route('/genre/<int:genre_id>/<int:user_id>/edit/', methods=['GET', 'POST'])
@login_required
def edit_genre(genre_id, user_id):
    """
    edit genre parameters
    """
    user = None
    if 'email' in login_session:
        user = get_user(login_session['email'])
    genre = session.query(Genre).filter_by(id = genre_id).one()
    # only genre creator can edit its description
    if user and user.id == genre.user_id:
        if request.method == 'POST':
            genre.name = request.form["name"]
            genre.poster_url = request.form["poster_url"]
            genre.description = request.form["description"]
            session.add(genre)
            session.commit()
            flash("The list %s has been edited" %genre.name)
            return redirect('/')
        else:
            return render_template("edit_genre.html", user=user, genre=genre)
    else:
        # user is not matching with the genre creator
        abort(401)

# delete genre page
@app.route('/genre/<int:genre_id>/<int:user_id>/delete/', methods=['GET', 'POST'])
@login_required
def delete_genre(genre_id, user_id):
    """
    delete genre
    """
    if 'email' in login_session:
        user = get_user(login_session['email'])
    genre = session.query(Genre).filter_by(id = genre_id).one()

    if user and user.id == genre.user_id:
        if request.method == 'POST':
            # get all movies of the genre
            movies = session.query(Movie).filter_by(genre_id = genre_id).all()
            for movie in movies:
                session.delete(movie)
            session.delete(genre)
            session.commit()
            flash("The list %s has been deleted" %genre.name)
            return redirect('/')
        else:
            return render_template("delete_genre.html", user=user, genre=genre)
    else:
        abort(401)

# add a movie page
@app.route('/genre/<int:genre_id>/<int:user_id>/new/', methods=['GET', 'POST'])
@login_required
def create_movie(genre_id, user_id):
    """
    create a new movie
    """
    if 'email' in login_session:
        user = get_user(login_session['email'])
    # retrieve genre
    genre = session.query(Genre).filter_by(id = genre_id).one()
    # accept post only if user is not None and user id matches with the genre
    if user and user.id == genre.user_id:
        if request.method == 'POST':
            new_movie = Movie(name=request.form["name"],
                storyline=request.form["storyline"],
                poster_url=request.form["poster_url"],
                trailer_url = request.form["trailer_url"],
                user_id=user_id,
                genre_id=genre_id)
            session.add(new_movie)
            session.commit()
            flash("A new movie %s added." %new_movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id, user=user))
        else:
            return render_template("create_movie.html", user=user, genre=genre)
    else:
        abort(401)

# show movie details
@app.route('/genre/<int:genre_id>/<int:movie_id>/')
def show_movie_details(genre_id, movie_id):
    """
    show movie details
    """
    user = None
    if 'email' in login_session:
        user = get_user(login_session['email'])
    movie = session.query(Movie).filter_by(id=movie_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    youtube_url = ""
    try:
        append = movie.trailer_url.split(".be/")[1]
        youtube_url = "https://www.youtube.com/embed/" + append
        return render_template("movie_details.html", movie=movie, url=youtube_url, user=user, genre_id=genre_id)
    except:
        print("No valid youtube URL")
        return render_template("movie_details.html", movie=movie, url="", genre_id=genre_id, user=user)


# edit movie page
@app.route('/genre/<int:genre_id>/<int:movie_id>/edit_movie', methods=['GET', 'POST'])
@login_required
def edit_movie(genre_id, movie_id):
    """
    edit movie info
    """
    user = None
    if 'email' in login_session:
        user = get_user(login_session['email'])
    # retrieve movie and genre
    try:
        movie = session.query(Movie).filter_by(id=movie_id).one()
        genre = session.query(Genre).filter_by(id=genre_id).one()
    except:
        return redirect('/')
    if user and user.id == movie.user_id:
        if request.method == 'POST':
            movie.name = request.form["name"]
            movie.poster_url = request.form["poster_url"]
            movie.storyline = request.form["storyline"]
            movie.trailer_url = request.form["trailer_url"]
            session.add(movie)
            session.commit()
            flash("The movie %s has been edited" %movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id))
        else:
            return render_template("edit_movie.html", movie=movie)
    else:
        abort(401)

# delete movie page (not completed)
@app.route('/genre/<int:genre_id>/<int:movie_id>/delete_movie', methods=['GET', 'POST'])
@login_required
def delete_movie(genre_id, movie_id):
    """
    edit movie info
    """
    if 'email' in login_session:
        user = get_user(login_session['email'])
    # retrieve movie and genre
    try:
        movie = session.query(Movie).filter_by(id=movie_id).one()
        genre = session.query(Genre).filter_by(id=genre_id).one()
    except:
        return redirect('/')
    if user and user.id == movie.user_id:
        if request.method == 'POST':
            session.delete(movie)
            session.commit()
            flash("The movie '%s' has been deleted" %movie.name)
            return redirect(url_for('show_movies_genre', genre_id=genre.id))
        else:
            return render_template("delete_movie.html", movie=movie, user=user)
    else:
        abort(401)

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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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
    output += ' " style = "width: 200px; height: 200px;border-radius: 100px;-webkit-border-radius: 100px;-moz-border-radius: 100px;"> '
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

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """
    Handles authentication and authorization for facebook
    authentication.
    """
    # state token validation
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'
                                            ), 401)
        response.headers['content-type'] = 'application/json'
        return response
    access_token = request.data

    # exchange client token for server token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web'][
        'app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web'][
        'app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?grant_type='
           'fb_exchange_token&client_id=%s&client_secret=%s&'
           'fb_exchange_token=%s'
           % (app_id, app_secret, access_token))
    http_ = httplib2.Http()
    result = http_.request(url, 'GET')[1]

    # use token to get info from fb api
    # userinfo_url = 'https://graph.facebook.com/v2.4/me'

    # Strip expire tag from access token
    token = result.split('&')[0]
    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign in
    # our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    http_ = httplib2.Http()
    result = http_.request(url, 'GET')[1]
    print "url sent for API access: %s" % url
    print "API JSON result: %s" % result

    data = json.loads(result)

    # populate login session
    login_session['username'] = data['name']
    print login_session['username']
    if 'email' in login_session:
        login_session['email'] = data['email']
    else:
        # it is possible for the user to not to have any email. So we will 
        # set username@facebook.com string as the email (guaranteed to be unique)
        login_session['email'] = data['name'] + '@facebook.com'
    login_session['facebook_id'] = data['id']
    login_session['provider'] = 'facebook'
    # get user profile pic
    url = ('https://graph.facebook.com/v2.4/me/picture?%s'
           '&redirect=0&height=200&width=200' % token)
    http_ = httplib2.Http()
    result = http_.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data['data']['url']

    # if the user exists get their user id otherwise create new user
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    # store the user id in the login session
    login_session['user_id'] = user_id
    # display welcome message for user
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px;'
    output += ' height: 200px;'
    output += 'border-radius: 100px;'
    output += '-webkit-border-radius: 100px;'
    output += '-moz-border-radius: 100px;"> '
    print "done!"
    print "email in fb:", login_session['email']
    flash("You are now logged in as %s" % login_session['username'])
    return output

def fbdisconnect():
    """ Log out of facebook """
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = ('https://graph.facebook.com/%s/'
           'permissions?access_token=%s'
           % (facebook_id, access_token))
    http_ = httplib2.Http()
    result = http_.request(url, 'DELETE')[1]
    return 'You have logged out.'

@app.route('/logout')
def disconnect():
    """ Handles the disconnection of all accounts """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        return redirect('/')
    else:
        return redirect('/')


def create_user(login_session):
    """
    Creates a new user and save in db.
    Returns its id. 
    """
    new_user = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    return new_user.id    


def get_user(email):
    """
    Gets user by its email. If the email does not match 
    returns None.
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None

def get_user_from_id(id):
    """
    Gets user from id. In case of no match returns None.
    """
    try:
        user = session.query(User).filter_by(id = id).one()
        return user
    except:
        return None

 
def get_user_id(email):
    """
    Gets user id associated with the input email
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port = 5000)
