from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

import re
import sqlite3
import os.path
import json

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'Flask%Crud#Application'

app.permanent_session_lifetime = timedelta(minutes=5)

# Enter your database connection details below
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db.sqlite")

# SqLite database connection
conn = sqlite3.connect(db_path, check_same_thread=False)

'''
# External database connection

mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = "localhost"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'demo_db'


# Initialize MySQL
mysql.init_app(app)
'''
# Opening movies.json file
here = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(here, 'static/movies.json')
f = open(filename)

movie_data = json.load(f)
movie_data.reverse()


@app.route('/', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for("home"))

    # Output message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        session.permanent = True

        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if user exists using MySQL
        # conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))

        # Fetch one record and return result
        user = cursor.fetchone()
        print(user)

        # If user exists in users table in the database
        if user and check_password_hash(user[4], password):

            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['firstname'] = user[0]
            session['username'] = user[3]

            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # user doesnt exist or username/password incorrect
            msg = 'Incorrect username/password! :/'

    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('firstname', None)
    session.pop('username', None)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM movies')
    conn.commit()

    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        # Create variables for easy access
        first = request.form['firstname']
        last = request.form['lastname']
        username = request.form['username']
        password = request.form['password']
        hasher = generate_password_hash(password)
        email = request.form['email']

        # Check if user exists using MySQL
        # conn = mysql.connect()    #MySql connector
        cursor = conn.cursor()

        # cursor.execute('SELECT * FROM users WHERE username = %s', (username,))  #MySql connect statement
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))  # SqLite Connect statement
        user = cursor.fetchone()

        # If user exists show error and validation checks
        if user:
            msg = 'Username/user already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # user doesn't exists and the form data is valid, now insert new user into users table
            # MySql Insert statement
            # cursor.execute('INSERT INTO users VALUES (%s, %s, %s, %s, %s)', (first, last, email, username, hash))

            # SqLite Insert Statement
            cursor.execute('INSERT INTO users (firstname, lastname, email, username, password) VALUES (?, ?, ?, ?, ?)',
                           (first, last, email, username, hasher,))
            conn.commit()
            # msg = 'You have successfully registered!'
            return render_template('index.html')

    elif request.method == "POST":
        # Form is empty... (no POST data)
        msg = 'Please fill all required fields!'

    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        unique_genres = []
        test_movie = {}
        cursor = conn.cursor()
        for i in range(1000):
            title = movie_data[i]['title']
            year = movie_data[i]['year']
            cast = ''
            genres = ''
            for member in movie_data[i]['cast']:
                cast += member + ' '
            for genre in movie_data[i]['genres']:
                if genre not in unique_genres:
                    unique_genres.append(genre)
                genres += genre + ' '
            cursor.execute('INSERT INTO movies (title, year, cast, genres) '
                           'VALUES (?, ?, ?, ?)',
                           (title, year, cast, genres))
        conn.commit()

        for genre in unique_genres:
            # this tweaking of the current_genre variable allows me to search for words containing the specified genre
            current_genre = '%'
            current_genre += genre
            current_genre += '%'

            # I have a small bug here. Genres with less than 100 movies are added to my dictionary too many time
            cursor.execute('SELECT * FROM movies WHERE genres LIKE ? ', (current_genre,))
            test_movie[current_genre[1:-1]] = cursor.fetchmany(100)

        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'], movies=test_movie, )

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the user info for the user so we can display it on the profile page
        # conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (session['username'],))
        user = cursor.fetchone()

        # Show the profile page with user info
        return render_template('profile.html', user=user)

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()
