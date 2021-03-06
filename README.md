# The Movie Catalogue #

The movie catalogue application. It demonstrates CRUD functionality and also third party 
authentication/authorization (Google) integrations for login and user permissions.
The web application uses SeaSurf to protect against CSRF attacks and provides CRUD functionality
on poster images of lists or movies. 

- Users can create and edit their own movies list. Each list has its own name, 
description and representative poster.
- Users can create movies inside their own lists of movies. Each movie has its name,
description, poster and trailer URL. 
- Non-logged in users may view all the lists and movies in the catalogues. They can also 
access JSON API endpoint.
- Logged in users can edit/delete their own lists or movies.
- Customized pages for Unauthorized Access or Server Exceptions. 

### Dependencies ###
- [Python 2.7][1]
- [Flask][2]
- [SQLAlchemy][3]
- [httplib2][4]
- [SeaSurf][5]

### Setting up OAuth2.0 ###
1. Sign up for a google account and set up a client id and secret. Visit: [http://console.developers.google.com](http://console.developers.google.com)
2. The client id needs to be replaced in line 23 of the login.html with client id obtained above.

### API Endpoints ###
- Aggregated movies data can be downloaded via API endpoints at the link http://localhost:5000/json or
http://localhost:5000/movies/json
- JSON endpoints for a single movie info are http://localhost:5000/json/movie/<int:movie_id> or
http://localhost:5000/movies/json/movie/<int:movie_id>
- JSON endpoints for a given list info are http://localhost:5000/json/genre/<int:genre_id> 
or http://localhost:5000/json/movies/genre/<int:genre_id>

### Running project ###
- Ensure you have the required software installed (see Requirements)
- Clone the repo: `git clone https://github.com/ashutoshpurushottam/The-Movie-Catalogue.git`
- Inside the repo in terminal navigate to the The-Movie-Catalogue directory
- Set up the database: `python database_setup.py`
- Populate the database: `python populate_database.py` 
- For running the code populate_database.py you will need to create an account in [TMDB][8] website
- You will need to create username, password and obtain api_key from the TMDB website and 
put them in a secret.py file with variable names username, password and api_key respectively. 
- If you want you can use skip the above two steps and use the database genremoviewithusers.db 
included in the repository. You can login and add your own lists and movies to the db. 
- Run the app: `python project.py`
- Navigate to the app via a web browser: http://localhost:5000
- To test the database edit edit test_database.py as per your requirement and run: `python test_database.py`

### Credits ###
- Front-end Framework: [Materialize Framework][6]
- Icons: [Font Awesome][7]
- Movie details and trailers: [TMDB][8]
- Flask Error Handling: http://damyanon.net/flask-series-logging/
- 413 Error handling: https://gist.github.com/bacher09/7231395
- Stacking movie or list cards : [Masonry JS Library][9]
- Scroll up button : http://html-tuts.com/back-to-top-button-jquery/


### TODO's ###
- Flask database migration code.
- Checks on form inputs. 
- Better stacking of movie cards.

### Info ###
- Mozilla Persona login was not attempted as it is being removed on November 30, 2016.

[1]: https://www.python.org/downloads/
[2]: http://flask.pocoo.org
[3]: http://www.sqlalchemy.org
[4]: https://github.com/jcgregorio/httplib2
[5]: https://flask-seasurf.readthedocs.org/en/latest/
[6]: http://materializecss.com/
[7]: http://fontawesome.io/
[8]: https://www.themoviedb.org/
[9]: http://masonry.desandro.com/
