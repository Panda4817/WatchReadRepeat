import os
import re

from movie_helpers import  MovieClient
from book_helpers import BookClient
from login_helpers import login_required
from apology_helpers import apology
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from validate_email import validate_email



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:////home/watchreadrepeat/watch_read_repeat/tracker.db")



# Make sure API key is set
if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY not set")

# Configure clients
movie_client = MovieClient()
book_client = BookClient()

# Global variables
_type = "type"
watching = False
watch_wish = False
imdb_id = "tt"
book_type = "type"
reading = False
read_wish = False
book_id = "b"


@app.route("/", methods=["GET"])
def index():
    if session.get("user_id") is None:
        # Forget any user_id
        session.clear()
        flash("This site only uses strictly necessary session cookies. By clicking agree or any other link on this site, you agree to the use of these cookies. PythonAnywhere has its own cookies policy. All policy links are in the footer.", "cookie")
        return render_template("index.html")
    else:
        return redirect("/dashboard")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to dashboard
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Goodbye! See you again soon!")
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # Check request method
    if request.method == "POST":

        # Get email from form
        email = request.form.get("email")

        # Ensure email was submitted
        if not email:
            return apology("Must provide email", 403)

        is_valid = validate_email(email_address=email, check_regex=True, check_mx=False, use_blacklist=True)
        if is_valid == False:
            return apology("Must provide valid email", 403)

        # Get username from form
        username = request.form.get("username")

        # Ensure username was submitted
        if not username:
            return apology("Must provide username", 403)

        #Check username only contains alphanumeric characters
        for i in range(len(username)):
            if not username[i].isalnum():
                return apology("Username must contain only letters or numbers!", 400)

        # search through database to check for the username
        rows = db.execute("SELECT username FROM users WHERE username = :username_check", username_check=username)

        # Check that the length of your result is 0, if not there is a match
        if len(rows) != 0:
            return apology("Username already taken", 409)

        # Get password from form
        password = request.form.get("password")

        # Ensure password was submitted and confirmation filled out
        if not password or not request.form.get("confirmation"):
            return apology("Must provide password", 403)

        # Check the length of the password is correct
        if len(password) < 6 or len(password) > 15:
            return apology("Password too short or too long", 400)

        # Created variable to keep track of uppercase, lowercase, number, special character and whitespace
        u = 0
        l = 0
        n = 0
        s = 0
        w = 0

        # Iterate over password and add 1 to each variable when condition met
        for i in range(len(password)):
            if password[i].isupper() == True:
                u += 1
            if password[i].islower() == True:
                l += 1
            if password[i].isdigit() == True:
                n += 1
            if password[i].isspace() == True:
                w += 1
            if password[i].isalnum() == False and password[i].isspace() == False:
                s += 1

        # Check password has the right number of numbers, special characters, lowercase and uppercase and no spaces
        if u == 0 or l == 0 or n == 0 or s == 0 or w > 0:
            return apology("Inavlid password", 400)

        # Check password field and conformation field match
        if password != request.form.get("confirmation"):
            return apology("Passwords do not match", 409)

        # Generate password hash
        hash = generate_password_hash(password)

        # Insert new data into database
        db.execute("INSERT INTO users (username, email, hash) VALUES (:username, :email, :hash)", username=username, email=email, hash=hash)

    # User reached route via GET (as by clicking a link)
    else:
        # Forget any user_id
        session.clear()

        return render_template("register.html")

    # Redirect user to login form with a flash message
    flash("You have sucessfully registered, now you can login")
    return render_template("login.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    # Check method
    if request.method == "POST":

        # Check if a name has been provided and save it in a variable
        if not request.form.get("name"):
            name = None
            user_id = None
        else:
            name = request.form.get("name")

            # search through database to check for the username
            rows = db.execute("SELECT * FROM users WHERE username = :username_check", username_check=name)

            # Check that the length of your result is 0, if not there is a match
            if len(rows) != 0:
                user_id = rows[0]['id']
            else:
                user_id = None

        # Check if email has been provided
        if not request.form.get("email"):
            return apology("Must provide email address", 403)
        else:
            email = request.form.get("email")

        is_valid = validate_email(email_address=email, check_regex=True, check_mx=False, use_blacklist=True)
        if is_valid == False:
            return apology("Must provide valid email", 403)

        # Check if textarea is filled out
        if not request.form.get("comments"):
            return apology("Must fill out comments", 403)
        else:
            comments = request.form.get("comments")

         # Insert new data into database
        db.execute("INSERT INTO contact (name, email, comments, contact_id) VALUES (:name, :email, :comments, :contact_id)",
                name=name, email=email, comments=comments, contact_id=user_id)

    # If method is get, render contact page
    else:
        contact_signal = True
        return render_template("contact.html", contact_signal=contact_signal)


    flash("Contact form sent!")
    return redirect("/contact")

@app.route("/dashboard")
@login_required
def dashboard():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    too_long = False
    if len(username) > 7:
        too_long = True

    data1 = db.execute("SELECT * FROM watched WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(data1) > 0:
        movie_data1 = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :data1_id", data1_id=data1[0]['imdb_id'])
    else:
        movie_data1 = [{"poster_url": "#", "title": "No data in watched list" }]

    data2 = db.execute("SELECT * FROM watching WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(data2) > 0:
        movie_data2 = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :data2_id", data2_id=data2[0]['imdb_id'])
    else:
        movie_data2 = [{"poster_url": "#", "title": "No data in watching list" }]

    data3 = db.execute("SELECT * FROM watch_wish WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(data3) > 0:
        movie_data3 = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :data3_id", data3_id=data3[0]['imdb_id'])
    else:
        movie_data3 = [{"poster_url": "#", "title": "No data in watch wishlist" }]

    book1 = db.execute("SELECT * FROM read WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(book1) > 0:
        book_1 = db.execute("SELECT * FROM books WHERE book_id = :data1_id", data1_id=book1[0]['book_id'])
    else:
        book_1 = [{"smallimage": "#", "title": "No data in read list" }]

    book2 = db.execute("SELECT * FROM reading WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(book2) > 0:
        book_2 = db.execute("SELECT * FROM books WHERE book_id = :data2_id", data2_id=book2[0]['book_id'])
    else:
        book_2 = [{"smallimage": "#", "title": "No data in reading list" }]

    book3 = db.execute("SELECT * FROM read_wish WHERE user_id = :session_id ORDER BY timestamp DESC LIMIT 1", session_id=session["user_id"])
    if len(book3) > 0:
        book_3 = db.execute("SELECT * FROM books WHERE book_id = :data3_id", data3_id=book3[0]['book_id'])
    else:
        book_3 = [{"smallimage": "#", "title": "No data in reading wishlist" }]

    both_watch = db.execute("SELECT * FROM movie_tv JOIN watched ON movie_tv.imdb_id = watched.imdb_id WHERE watched.user_id = :user_id ORDER BY watched.rating DESC LIMIT 5",
    user_id=session['user_id'])
    if len(both_watch) == 0:
        both_watch = [{'title': 'Nothing watched yet', 'rating': 'None'}]
    x = 1
    for row in both_watch:
        row['number'] = x
        x = x + 1

    movies = db.execute("SELECT * FROM movie_tv JOIN watched ON movie_tv.imdb_id = watched.imdb_id WHERE watched.user_id = :user_id AND movie_tv.type = :type_s ORDER BY watched.rating DESC LIMIT 5",
    user_id=session['user_id'], type_s='movie')
    if len(movies) == 0:
        movies = [{'title': 'No movies watched yet', 'rating': 'None'}]
    x = 1
    for row in movies:
        row['number'] = x
        x = x + 1


    tv_shows = db.execute("SELECT * FROM movie_tv JOIN watched ON movie_tv.imdb_id = watched.imdb_id WHERE watched.user_id = :user_id AND movie_tv.type = :type_s ORDER BY watched.rating DESC LIMIT 5",
    user_id=session['user_id'], type_s='tv show')
    if len(tv_shows) == 0:
        tv_shows = [{'title': 'No tv shows watched yet', 'rating': 'None'}]

    x = 1
    for row in tv_shows:
        row['number'] = x
        x = x + 1



    both_read = db.execute("SELECT * FROM books JOIN read ON books.book_id = read.book_id WHERE read.user_id = :user_id ORDER BY read.rating DESC LIMIT 5",
    user_id=session['user_id'])
    if len(both_read) == 0:
        both_read = [{'title': 'Nothing read yet', 'rating': 'None'}]

    x = 1
    for row in both_read:
        row['number'] = x
        x = x + 1

    fiction = db.execute("SELECT * FROM books JOIN read ON books.book_id = read.book_id WHERE read.user_id = :user_id AND books.type = :type_s ORDER BY read.rating DESC LIMIT 5",
    user_id=session['user_id'], type_s='fiction')
    if len(fiction) == 0:
        fiction = [{'title': 'No fiction books read yet', 'rating': 'None'}]


    x = 1
    for row in fiction:
        row['number'] = x
        x = x + 1

    non_fiction = db.execute("SELECT * FROM books JOIN read ON books.book_id = read.book_id WHERE read.user_id = :user_id AND books.type = :type_s ORDER BY read.rating DESC LIMIT 5",
    user_id=session['user_id'], type_s='non-fiction')
    if len(non_fiction) == 0:
        non_fiction = [{'title': 'No non-fiction books read yet', 'rating': 'None'}]

    x = 1
    for row in non_fiction:
        row['number'] = x
        x = x + 1



    barRf = db.execute("select count(books.book_id) as fread from books join read on books.book_id = read.book_id where read.user_id = :user_id and books.type = 'fiction'",
        user_id=session["user_id"])
    barRnf = db.execute("select count(books.book_id) as nfread from books join read on books.book_id = read.book_id where read.user_id = :user_id and books.type = 'non-fiction'",
        user_id=session["user_id"])
    barRef = db.execute("select count(books.book_id) as freading from books join reading on books.book_id = reading.book_id where reading.user_id = :user_id and books.type = 'fiction'",
        user_id=session["user_id"])
    barRenf = db.execute("select count(books.book_id) as nfreading from books join reading on books.book_id = reading.book_id where reading.user_id = :user_id and books.type = 'non-fiction'",
        user_id=session["user_id"])
    barRwf = db.execute("select count(books.book_id) as fread_wish from books join read_wish on books.book_id = read_wish.book_id where read_wish.user_id = :user_id and books.type = 'fiction'",
        user_id=session["user_id"])
    barRwnf = db.execute("select count(books.book_id) as nfread_wish from books join read_wish on books.book_id = read_wish.book_id where read_wish.user_id = :user_id and books.type = 'non-fiction'",
        user_id=session["user_id"])

    barWm = db.execute("select count(movie_tv.imdb_id) as mwatched from movie_tv join watched on movie_tv.imdb_id = watched.imdb_id where watched.user_id = :user_id and movie_tv.type = 'movie'",
        user_id=session["user_id"])
    barWt = db.execute("select count(movie_tv.imdb_id) as twatched from movie_tv join watched on movie_tv.imdb_id = watched.imdb_id where watched.user_id = :user_id and movie_tv.type = 'tv show'",
        user_id=session["user_id"])
    barWdm = db.execute("select count(movie_tv.imdb_id) as mwatching from movie_tv join watching on movie_tv.imdb_id = watching.imdb_id where watching.user_id = :user_id and movie_tv.type = 'movie'",
        user_id=session["user_id"])
    barWdt = db.execute("select count(movie_tv.imdb_id) as twatching from movie_tv join watching on movie_tv.imdb_id = watching.imdb_id where watching.user_id = :user_id and movie_tv.type = 'tv show'",
        user_id=session["user_id"])
    barWwm = db.execute("select count(movie_tv.imdb_id) as mwatch_wish from movie_tv join watch_wish on movie_tv.imdb_id = watch_wish.imdb_id where watch_wish.user_id = :user_id and movie_tv.type = 'movie'",
        user_id=session["user_id"])
    barWwt = db.execute("select count(movie_tv.imdb_id) as twatch_wish from movie_tv join watch_wish on movie_tv.imdb_id = watch_wish.imdb_id where watch_wish.user_id = :user_id and movie_tv.type = 'tv show'",
        user_id=session["user_id"])

    return render_template("dashboard.html",
        username=username, too_long=too_long, img1=movie_data1[0]['poster_url'], title1=movie_data1[0]['title'],
        img2=movie_data2[0]['poster_url'], title2=movie_data2[0]['title'],
        img3=movie_data3[0]['poster_url'], title3=movie_data3[0]['title'],
        cover1=book_1[0]['smallimage'], cover2=book_2[0]['smallimage'], cover3=book_3[0]['smallimage'],
        book1=book_1[0]['title'], book2=book_2[0]['title'], book3=book_3[0]['title'],
        fread=barRf[0]['fread'], nfread=barRnf[0]['nfread'], freading=barRef[0]['freading'], nfreading=barRenf[0]['nfreading'],
        fread_wish=barRwf[0]['fread_wish'], nfread_wish=barRwnf[0]['nfread_wish'],
        mwatched=barWm[0]['mwatched'], twatched=barWt[0]['twatched'], mwatching=barWdm[0]['mwatching'], twatching=barWdt[0]['twatching'],
        mwatch_wish=barWwm[0]['mwatch_wish'], twatch_wish=barWwt[0]['twatch_wish'],
        both_watch=both_watch, both_read=both_read, movies=movies, tv_shows=tv_shows, fiction=fiction, non_fiction=non_fiction)

@app.route("/profile")
@login_required
def profile():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    email = user[0]["email"]
    if user[0]["market"] == "yes":
        market = True
    else:
        market = False
    return render_template("profile.html", username=username, email=email, market=market)

@app.route("/profile-username", methods=["POST"])
@login_required
def profile_username():

    # Get new username
    new_username = request.form.get("new_username")

    # Check new user name inputed in both fields
    if not new_username or not request.form.get("Uconfirmation"):
        return apology("Must provide new username", 403)

    # search through database to check for the username
    rows = db.execute("SELECT username FROM users WHERE username = :username_check", username_check=new_username)

    # Check that the length of your result is 0, if not there is a match
    if len(rows) != 0:
        return apology("Username already taken", 409)

    # Check both username fields match
    if new_username != request.form.get("Uconfirmation"):
        return apology("New username fields do not match", 400)

    db.execute("UPDATE users SET username = :new_username WHERE id = :user_id", new_username=new_username, user_id=session["user_id"])


    flash("Username changed sucessfully!")
    return redirect("/profile")

@app.route("/profile-email", methods=["POST"])
@login_required
def profile_email():

    # Get new email
    new_email = request.form.get("new_email")

    # Check new email inputed in both fields
    if not new_email or not request.form.get("Econfirmation"):
        return apology("Must provide new email", 403)

    # Check both email fields match
    if new_email != request.form.get("Econfirmation"):
        return apology("New email fields do not match", 400)

    db.execute("UPDATE users SET email = :new_email WHERE id = :user_id", new_email=new_email, user_id=session["user_id"])


    flash("Email changed sucessfully!")
    return redirect("/profile")

@app.route("/profile-password", methods=["POST"])
@login_required
def profile_password():
    # Get currenct passord
    input_password = request.form.get("current_password")

    # Check current password filled out
    if not input_password:
        return apology("Must provide current password", 403)

    # Get user data
    user = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

    # Check hash of password matches database stored one
    if not check_password_hash(user[0]["hash"], request.form.get("current_password")):
        return apology("Current password invalid", 400)

    # Get new password from the form
    new_password = request.form.get("new_password")

    # Make sure new password fields are filled out
    if not new_password or not request.form.get("confirmation"):
        return apology("Must provide new password", 403)

    # Check length of new password
    if len(new_password) < 6 or len(new_password) > 15:
        return apology("password too short or too long", 400)

    # Variables to keep track of different type of characters
    u = 0
    l = 0
    n = 0
    s = 0
    w = 0

    # Iterate over new password and add 1 to a variable when it finds lowercase, uppercase, special character, number or whitespace
    for i in range(len(new_password)):
        if new_password[i].isupper() == True:
            u += 1
        if new_password[i].islower() == True:
            l += 1
        if new_password[i].isdigit() == True:
            n += 1
        if new_password[i].isspace() == True:
            w += 1
        if new_password[i].isalnum() == False and new_password[i].isspace() == False:
            s += 1

    # Check password for right number of each type of character and no white spaces
    if u == 0 or l == 0 or n == 0 or s == 0 or w > 0:
        return apology("Invalid new password", 400)

    # Check new passwords match
    if new_password != request.form.get("confirmation"):
        return apology("New password fields do not match", 409)

    # Create hash of new password
    hash_new = generate_password_hash(new_password)

    # Update user hash data
    db.execute("UPDATE users SET hash = :hash_new WHERE id = :user_id", hash_new=hash_new, user_id=user[0]["id"])


    flash("Password updated sucessfully!")
    return redirect("/profile")

@app.route("/profile-market", methods=["POST"])
@login_required
def profile_market():
    answer = request.form.get("marketopt")
    db.execute("UPDATE users SET market = :new_market WHERE id = :user_id", new_market=answer, user_id=session["user_id"])


    flash("Marketing preference updated!")
    return redirect("/profile")

@app.route("/watched", methods=["GET"])
@login_required
def watched():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM movie_tv JOIN watched ON movie_tv.imdb_id = watched.imdb_id WHERE watched.user_id = :user_id",
        user_id=user[0]["id"])
    return render_template("watched.html", username=username, info=info)

@app.route("/title-search", methods=["POST"])
@login_required
def title_search():
    # Get title from form
    title = request.form.get("title")

    # Check title has been entered
    if not title:
        return apology("Must provide title", 403)

    # Retrieve user type input movie or tv show
    global _type
    _type = request.form.get("type")

    #Call to api to retrieve search results
    results = movie_client.search_titles(title)

    return render_template("search-results.html", results=results)

@app.route("/confirm-watched", methods=["POST"])
@login_required
def confirm_watched():
    global imdb_id
    imdb_id = request.form.get('imdb_id')

    # Check watching and watch-wishlist databases first
    check_watching  = db.execute("SELECT * FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)
    check_wish  = db.execute("SELECT * FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    check_watched  = db.execute("SELECT * FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_watched) != 0:
        message = "Already in watched!"
        return render_template("apology-modal.html", message=message)

    if len(check_watching) == 0 and len(check_wish) == 0:
        # Make the call to the api
        confirm_result = movie_client.get_film(imdb_id)

    if len(check_watching) != 0:
        confirm_result = db.execute("SELECT * FROM movie_tv JOIN watching ON movie_tv.imdb_id = watching.imdb_id WHERE watching.user_id = :user_id AND watching.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        global watching
        watching = True

    if len(check_wish) != 0:
        confirm_result = db.execute("SELECT * FROM movie_tv JOIN watch_wish ON movie_tv.imdb_id = watch_wish.imdb_id WHERE watch_wish.user_id = :user_id AND watch_wish.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        global watch_wish
        watch_wish = True

    return render_template("confirm-watched.html", result=confirm_result, _type=_type)

@app.route("/add-watched", methods=["POST"])
@login_required
def add_watched():
    # Get rating
    rating = request.form.get("rating")
    global imdb_id
    global watching
    global watch_wish
    global _type
    # Check bools set earlier
    if watching == False and watch_wish == False:
        add = movie_client.get_film(imdb_id)
        db.execute("INSERT INTO watched (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user_id"], imdb_id=imdb_id, rating=rating)
        imdb_url = 'https://www.imdb.com/title/'+ add["id"]
        check_duplicate = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
        if len(check_duplicate) == 0:
            db.execute("INSERT INTO movie_tv VALUES (:imdb_id, :mediatype, :title, :year, :length, :plot, :poster_url, :imdb_link)",
                imdb_id=imdb_id, mediatype=_type, title=add["title"], year=add["year"], length=add["length"], plot=add["plot"], poster_url=add["poster"], imdb_link=imdb_url)
    if watching == True:
        add = db.execute("SELECT * FROM movie_tv JOIN watching ON movie_tv.imdb_id = watching.imdb_id WHERE watching.user_id = :user_id AND watching.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("DELETE FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("INSERT INTO watched (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user-id"], imdb_id=imdb_id, rating=rating)
    if watch_wish == True:
        add = db.execute("SELECT * FROM movie_tv JOIN watch_wish ON movie_tv.imdb_id = watch_wish.imdb_id WHERE watch_wish.user_id = :user_id AND watch_wish.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("DELETE FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("INSERT INTO watched (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user_id"], imdb_id=imdb_id, rating=rating)

    _type = "type"
    watching = False
    watch_wish = False
    imdb_id = "tt"


    flash("Added sucessfully!")
    return redirect("/watched")

@app.route("/remove-watched", methods=["POST"])
@login_required
def remove_watched():
    global imdb_id
    imdb_id = request.form.get("remove")
    db.execute("DELETE FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)

    imdb_id = "tt"


    flash("Removed sucessfully!")
    return redirect("/watched")

@app.route("/type-watched", methods=["POST"])
@login_required
def type_watched():
    global imdb_id
    imdb_id = request.form.get("typeChange")

    global _type

    data = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
    _type = data[0]['type']

    return render_template("type-watched.html", _type=_type)

@app.route("/change-type", methods=["POST"])
@login_required
def change_type():
    global imdb_id
    global _type
    _type = request.form.get("type")

    db.execute("UPDATE movie_tv SET type = :new_type WHERE imdb_id = :imdb_id", new_type=_type, imdb_id=imdb_id)

    _type = "type"
    imdb_id = "tt"


    flash("Type updated sucessfully!")
    return redirect("/watched")

@app.route("/rating-watched", methods=["POST"])
@login_required
def rating_watched():
    global imdb_id
    imdb_id = request.form.get("ratingChange")

    return render_template("rating-watched.html")

@app.route("/change-rating", methods=["POST"])
@login_required
def change_rating():
    global imdb_id
    rating = request.form.get("rating")

    db.execute("UPDATE watched SET rating = :new_rating WHERE imdb_id = :imdb_id AND user_id = :user_id", new_rating=rating, imdb_id=imdb_id, user_id=session["user_id"])

    imdb_id = "tt"


    flash("Rating updated sucessfully!")
    return redirect("/watched")

@app.route("/watching", methods=["GET"])
@login_required
def watching_page():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM movie_tv JOIN watching ON movie_tv.imdb_id = watching.imdb_id WHERE watching.user_id = :user_id",
        user_id=user[0]["id"])
    return render_template("watching.html", username=username, info=info)

@app.route("/confirm-watching", methods=["POST"])
@login_required
def confirm_watching():
    global imdb_id
    imdb_id = request.form.get('imdb_id')

    # Check watching and watch-wishlist databases first

    check_watching  = db.execute("SELECT * FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_watching) != 0:
        message = "Already in watching!"
        return render_template("apology-modal.html", message=message)

    check_watched  = db.execute("SELECT * FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_watched) != 0:
        message = "Already added to watched!"
        return render_template("apology-modal.html", message=message)

    check_wish  = db.execute("SELECT * FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_wish) == 0:
        # Make the call to the api
        confirm_result = movie_client.get_film(imdb_id)

    if len(check_wish) != 0:
        confirm_result = db.execute("SELECT * FROM movie_tv JOIN watch_wish ON movie_tv.imdb_id = watch_wish.imdb_id WHERE watch_wish.user_id = :user_id AND watch_wish.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        global watch_wish
        watch_wish = True

    return render_template("confirm-watching.html", result=confirm_result, _type=_type)

@app.route("/add-watching", methods=["POST"])
@login_required
def add_watching():
    # Get rating
    rating = request.form.get("rating")
    global imdb_id
    global watch_wish
    global _type
    # Check bools set earlier
    if watch_wish == False:
        add = movie_client.get_film(imdb_id)
        db.execute("INSERT INTO watching (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user_id"], imdb_id=imdb_id, rating=rating)
        imdb_url = 'https://www.imdb.com/title/'+ add["id"]
        check_duplicate = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
        if len(check_duplicate) == 0:
            db.execute("INSERT INTO movie_tv VALUES (:imdb_id, :mediatype, :title, :year, :length, :plot, :poster_url, :imdb_link)",
                imdb_id=imdb_id, mediatype=_type, title=add["title"], year=add["year"], length=add["length"], plot=add["plot"], poster_url=add["poster"], imdb_link=imdb_url)

    if watch_wish == True:
        add = db.execute("SELECT * FROM movie_tv JOIN watch_wish ON movie_tv.imdb_id = watch_wish.imdb_id WHERE watch_wish.user_id = :user_id AND watch_wish.imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("DELETE FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
        db.execute("INSERT INTO watching (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user_id"], imdb_id=imdb_id, rating=rating)

    _type = "type"
    watch_wish = False
    imdb_id = "tt"


    flash("Added sucessfully!")
    return redirect("/watching")

@app.route("/remove-watching", methods=["POST"])
@login_required
def remove_watching():
    global imdb_id
    imdb_id = request.form.get("remove")
    db.execute("DELETE FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)

    imdb_id = "tt"


    flash("Removed sucessfully!")
    return redirect("/watching")

@app.route("/type-watching", methods=["POST"])
@login_required
def type_watching():
    global imdb_id
    imdb_id = request.form.get("typeChange")

    global _type

    data = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
    _type = data[0]['type']

    return render_template("type-watching.html", _type=_type)

@app.route("/change-type-watching", methods=["POST"])
@login_required
def change_type_watching():
    global imdb_id
    global _type
    _type = request.form.get("type")

    db.execute("UPDATE movie_tv SET type = :new_type WHERE imdb_id = :imdb_id", new_type=_type, imdb_id=imdb_id)

    _type = "type"
    imdb_id = "tt"


    flash("Type updated sucessfully!")
    return redirect("/watching")

@app.route("/rating-watching", methods=["POST"])
@login_required
def rating_watching():
    global imdb_id
    imdb_id = request.form.get("ratingChange")

    return render_template("rating-watching.html")

@app.route("/change-rating-watching", methods=["POST"])
@login_required
def change_rating_watching():
    global imdb_id
    rating = request.form.get("rating")

    db.execute("UPDATE watching SET rating = :new_rating WHERE imdb_id = :imdb_id AND user_id = :user_id", new_rating=rating, imdb_id=imdb_id, user_id=session["user_id"])

    imdb_id = "tt"


    flash("Rating updated sucessfully!")
    return redirect("/watching")

@app.route("/finished-watching", methods=["POST"])
@login_required
def finished_watching():
    global imdb_id
    imdb_id = request.form.get("finished")
    data = db.execute("SELECT * FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("DELETE FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("INSERT INTO watched (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
            user_id=session["user_id"], imdb_id=imdb_id, rating=data[0]['rating'])


    imdb_id = "tt"


    flash("Moved to watched!")
    return redirect("/watching")

@app.route("/watch-wish", methods=["GET"])
@login_required
def watch_wishlist():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM movie_tv JOIN watch_wish ON movie_tv.imdb_id = watch_wish.imdb_id WHERE watch_wish.user_id = :user_id",
        user_id=user[0]["id"])
    return render_template("watch-wish.html", username=username, info=info)

@app.route("/confirm-watch-wishlist", methods=["POST"])
@login_required
def confirm_watch_wishlist():
    global imdb_id
    imdb_id = request.form.get('imdb_id')

    check_watch_wish  = db.execute("SELECT * FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_watch_wish) != 0:
        message = "Already in wishslist!"
        return render_template("apology-modal.html", message=message)

    check_watching  = db.execute("SELECT * FROM watching WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)
    check_watched  = db.execute("SELECT * FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session['user_id'], imdb_id=imdb_id)

    if len(check_watching) != 0 or len(check_watched) != 0:
        message = "Already added to watched or watching!"
        return render_template("apology-modal.html", message=message)

    confirm_result = movie_client.get_film(imdb_id)

    return render_template("confirm-watch-wishlist.html", result=confirm_result, _type=_type)

@app.route("/add-watch-wishlist", methods=["POST"])
@login_required
def add_watch_wishlist():
    global imdb_id
    global _type

    add = movie_client.get_film(imdb_id)
    # Check watched and watching databse


    db.execute("INSERT INTO watch_wish (user_id, imdb_id) VALUES (:user_id, :imdb_id)",
        user_id=session["user_id"], imdb_id=imdb_id)
    imdb_url = 'https://www.imdb.com/title/'+ add["id"]
    check_duplicate = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
    if len(check_duplicate) == 0:
        db.execute("INSERT INTO movie_tv VALUES (:imdb_id, :mediatype, :title, :year, :length, :plot, :poster_url, :imdb_link)",
            imdb_id=imdb_id, mediatype=_type, title=add["title"], year=add["year"], length=add["length"], plot=add["plot"], poster_url=add["poster"], imdb_link=imdb_url)

    _type = "type"
    imdb_id = "tt"


    flash("Added sucessfully!")
    return redirect("/watch-wish")

@app.route("/remove-watch-wishlist", methods=["POST"])
@login_required
def remove_watch_wishlist():
    global imdb_id
    imdb_id = request.form.get("remove")
    db.execute("DELETE FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
            user_id=session["user_id"], imdb_id=imdb_id)

    imdb_id = "tt"


    flash("Removed sucessfully!")
    return redirect("/watch-wish")

@app.route("/type-watch-wishlist", methods=["POST"])
@login_required
def type_watch_wishlist():
    global imdb_id
    imdb_id = request.form.get("typeChange")

    global _type

    data = db.execute("SELECT * FROM movie_tv WHERE imdb_id = :imdb_id", imdb_id=imdb_id)
    _type = data[0]['type']

    return render_template("type-watch-wishlist.html", _type=_type)

@app.route("/change-type-watch-wishlist", methods=["POST"])
@login_required
def change_type_watch_wishlist():
    global imdb_id
    global _type
    _type = request.form.get("type")

    db.execute("UPDATE movie_tv SET type = :new_type WHERE imdb_id = :imdb_id", new_type=_type, imdb_id=imdb_id)

    _type = "type"
    imdb_id = "tt"


    flash("Type updated sucessfully!")
    return redirect("/watch-wish")


@app.route("/Change2Watching", methods=["POST"])
@login_required
def change2watching_step1():
    global imdb_id
    imdb_id = request.form.get("watchingChange")

    return render_template("change2watching.html")

@app.route("/change2watchingAdd", methods=["POST"])
@login_required
def change2watching_stepAdd():
    global imdb_id
    rating = request.form.get('rating')

    data = db.execute("SELECT * FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
    user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("DELETE FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
    user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("INSERT INTO watching (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
    user_id=session["user_id"], imdb_id=imdb_id, rating=rating)

    imdb_id = "tt"


    flash("Moved to watching")
    return redirect("/watch-wish")

@app.route("/Change2Watched", methods=["POST"])
@login_required
def change2watched_step1():
    global imdb_id
    imdb_id = request.form.get("watchedChange")

    return render_template("change2watched.html")

@app.route("/change2watchedAdd", methods=["POST"])
@login_required
def change2watched_stepAdd():
    global imdb_id
    rating = request.form.get('rating')

    data = db.execute("SELECT * FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("DELETE FROM watch_wish WHERE user_id = :user_id AND imdb_id = :imdb_id",
        user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("INSERT INTO watched (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
        user_id=session["user_id"], imdb_id=imdb_id, rating=rating)

    imdb_id = "tt"

    flash("Moved to watched")
    return redirect("/watch-wish")

@app.route("/read", methods=["GET"])
@login_required
def read():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM books JOIN read ON books.book_id = read.book_id WHERE read.user_id = :user_id",
        user_id=user[0]["id"])

    return render_template("read.html", username=username, info=info)

@app.route("/search-book", methods=["POST"])
@login_required
def book_search():
    keywords = request.form.get('keywords')
    if not keywords:
        return apology("Must provide keywords for book search!", 403)

    exactkeywords = request.form.get('exactkeywords')
    if exactkeywords:
        keywords = '"'+keywords+'"'

    title = request.form.get('title')
    if title:
        keywords = 'intitle:'+keywords

    global book_type
    book_type = request.form.get('type')

    authors = request.form.get('authors')
    exactauthors = request.form.get('exactauthors')
    if authors:
        if exactauthors:
            authors = '"'+authors+'"'
        keywords = keywords+'+inauthor:'+authors

    publisher = request.form.get('publisher')
    exactpublisher = request.form.get('exactpublisher')
    if publisher:
        if exactpublisher:
            publisher = '"'+publisher+'"'
        keywords = keywords+'+inpublisher:'+publisher

    subject = request.form.get('subject')
    exactsubject = request.form.get('exactsubject')
    if subject:
        if exactsubject:
            subject = '"'+subject+'"'
        keywords = keywords+'+subject:'+subject

    isbn = request.form.get('isbn')
    if isbn:
        keywords = keywords+'+isbn:'+isbn

    results = book_client.search_any(keywords)

    return render_template("book-search-results.html", results=results)

@app.route("/confirm-read", methods=["POST"])
@login_required
def confirm_read():
    global book_id
    book_id = request.form.get('book_id')

    # Check watching and watch-wishlist databases first
    check_reading  = db.execute("SELECT * FROM reading WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)
    check_wish  = db.execute("SELECT * FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    check_read  = db.execute("SELECT * FROM read WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    if len(check_read) != 0:
        message = "Already in read!"
        return render_template("apology-modal.html", message=message)

    if len(check_reading) == 0 and len(check_wish) == 0:
        # Make the call to the api
        confirm_result = book_client.get_id(book_id)

    if len(check_reading) != 0:
        confirm_result = db.execute("SELECT * FROM books JOIN reading ON books.book_id = reading.book_id WHERE reading.user_id = :user_id AND reading.book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        global reading
        reading = True

    if len(check_wish) != 0:
        confirm_result = db.execute("SELECT * FROM books JOIN read_wish ON books.book_id = read_wish.book_id WHERE read_wish.user_id = :user_id AND read_wish.book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        global read_wish
        read_wish = True

    return render_template("confirm-read.html", row=confirm_result, _type=book_type)

@app.route("/add-read", methods=["POST"])
@login_required
def add_read():
    # Get rating
    rating = request.form.get("rating")
    global book_id
    global reading
    global read_wish
    global book_type
    # Check bools set earlier
    if reading == False and read_wish == False:
        add = book_client.get_id(book_id)
        db.execute("INSERT INTO read (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=rating)
        check_duplicate = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
        if len(check_duplicate) == 0:
            db.execute("INSERT INTO books VALUES (:book_id, :title, :authors, :publisher, :description, :smallimage, :mediumimage, :largeimage, :booktype)",
                book_id=book_id, title=add["title"], authors=add["authors"], publisher=add["publisher"], description=add["description"], smallimage=add["smallimage"], mediumimage=add["mediumimage"], largeimage=add["largeimage"], booktype=book_type )
    if reading == True:
        db.execute("DELETE FROM reading WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        db.execute("INSERT INTO read (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=rating)
    if read_wish == True:
        db.execute("DELETE FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        db.execute("INSERT INTO read (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=rating)

    book_type = "type"
    reading = False
    read_wish = False
    book_id = "b"

    flash("Added sucessfully!")
    return redirect("/read")

@app.route("/remove-read", methods=["POST"])
@login_required
def remove_read():
    global book_id
    book_id = request.form.get("remove")
    db.execute("DELETE FROM read WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)

    book_id = "b"

    flash("Removed sucessfully!")
    return redirect("/read")

@app.route("/type-read", methods=["POST"])
@login_required
def type_read():
    global book_id
    book_id = request.form.get("typeChange")

    global book_type

    data = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
    book_type = data[0]['type']

    return render_template("type-read.html", _type=book_type)

@app.route("/change-type-read", methods=["POST"])
@login_required
def change_type_read():
    global book_id
    global book_type
    book_type = request.form.get("type")

    db.execute("UPDATE books SET type = :new_type WHERE book_id = :book_id", new_type=book_type, book_id=book_id)

    book_type = "type"
    book_id = "b"

    flash("Type updated sucessfully!")
    return redirect("/read")

@app.route("/rating-read", methods=["POST"])
@login_required
def rating_read():
    global book_id
    book_id = request.form.get("ratingChange")

    return render_template("rating-read.html")

@app.route("/change-rating-read", methods=["POST"])
@login_required
def change_rating_read():
    global book_id
    rating = request.form.get("rating")

    db.execute("UPDATE read SET rating = :new_rating WHERE book_id = :book_id AND user_id = :user_id", new_rating=rating, book_id=book_id, user_id=session["user_id"])

    book_id = "b"

    flash("Rating updated sucessfully!")
    return redirect("/read")

@app.route("/reading", methods=["GET"])
@login_required
def reading_page():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM books JOIN reading ON books.book_id = reading.book_id WHERE reading.user_id = :user_id",
        user_id=user[0]["id"])

    return render_template("reading.html", username=username, info=info)


@app.route("/confirm-reading", methods=["POST"])
@login_required
def confirm_reading():
    global book_id
    book_id = request.form.get('book_id')

    # Check watching and watch-wishlist databases first
    check_reading  = db.execute("SELECT * FROM reading WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)
    check_wish  = db.execute("SELECT * FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    check_read  = db.execute("SELECT * FROM read WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    if len(check_read) != 0 or len(check_reading) != 0:
        message = "Already in read or reading lists!"
        return render_template("apology-modal.html", message=message)

    if len(check_wish) == 0:
        # Make the call to the api
        confirm_result = book_client.get_id(book_id)

    if len(check_wish) != 0:
        confirm_result = db.execute("SELECT * FROM books JOIN read_wish ON books.book_id = read_wish.book_id WHERE read_wish.user_id = :user_id AND read_wish.book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        global read_wish
        read_wish = True

    return render_template("confirm-reading.html", row=confirm_result, _type=book_type)

@app.route("/add-reading", methods=["POST"])
@login_required
def add_reading():
    # Get rating
    rating = request.form.get("rating")
    global book_id
    global reading
    global read_wish
    global book_type
    # Check bools set earlier
    if read_wish == False:
        add = book_client.get_id(book_id)
        db.execute("INSERT INTO reading (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=rating)
        check_duplicate = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
        if len(check_duplicate) == 0:
            db.execute("INSERT INTO books VALUES (:book_id, :title, :authors, :publisher, :description, :smallimage, :mediumimage, :largeimage, :booktype)",
                book_id=book_id, title=add["title"], authors=add["authors"], publisher=add["publisher"], description=add["description"], smallimage=add["smallimage"], mediumimage=add["mediumimage"], largeimage=add["largeimage"], booktype=book_type )

    if read_wish == True:
        db.execute("DELETE FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
        db.execute("INSERT INTO reading (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=rating)

    book_type = "type"
    reading = False
    read_wish = False
    book_id = "b"

    flash("Added sucessfully!")
    return redirect("/reading")

@app.route("/remove-reading", methods=["POST"])
@login_required
def remove_reading():
    global book_id
    book_id = request.form.get("remove")
    db.execute("DELETE FROM reading WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)

    book_id = "b"

    flash("Removed sucessfully!")
    return redirect("/reading")

@app.route("/type-reading", methods=["POST"])
@login_required
def type_reading():
    global book_id
    book_id = request.form.get("typeChange")

    global book_type

    data = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
    book_type = data[0]['type']

    return render_template("type-reading.html", _type=book_type)

@app.route("/change-type-reading", methods=["POST"])
@login_required
def change_type_reading():
    global book_id
    global book_type
    book_type = request.form.get("type")

    db.execute("UPDATE books SET type = :new_type WHERE book_id = :book_id", new_type=book_type, book_id=book_id)

    book_type = "type"
    book_id = "b"

    flash("Type updated sucessfully!")
    return redirect("/reading")

@app.route("/rating-reading", methods=["POST"])
@login_required
def rating_reading():
    global book_id
    book_id = request.form.get("ratingChange")

    return render_template("rating-reading.html")

@app.route("/change-rating-reading", methods=["POST"])
@login_required
def change_rating_reading():
    global book_id
    rating = request.form.get("rating")

    db.execute("UPDATE reading SET rating = :new_rating WHERE book_id = :book_id AND user_id = :user_id", new_rating=rating, book_id=book_id, user_id=session["user_id"])

    book_id = "b"

    flash("Rating updated sucessfully!")
    return redirect("/reading")

@app.route("/finished-reading", methods=["POST"])
@login_required
def finished_reading():
    global book_id
    book_id = request.form.get("finished")
    data = db.execute("SELECT * FROM reading WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
    db.execute("DELETE FROM reading WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)
    db.execute("INSERT INTO read (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
            user_id=session["user_id"], book_id=book_id, rating=data[0]['rating'])


    book_id = "b"

    flash("Moved to read list!")
    return redirect("/reading")

@app.route("/read-wish", methods=["GET"])
@login_required
def read_wish_page():
    user = db.execute("SELECT * FROM users WHERE id = :session_id", session_id=session["user_id"])
    username = user[0]["username"]
    info = db.execute("SELECT * FROM books JOIN read_wish ON books.book_id = read_wish.book_id WHERE read_wish.user_id = :user_id",
        user_id=user[0]["id"])

    return render_template("read-wish.html", username=username, info=info)

@app.route("/confirm-read-wish", methods=["POST"])
@login_required
def confirm_read_wish():
    global book_id
    book_id = request.form.get('book_id')

    # Check watching and watch-wishlist databases first
    check_reading  = db.execute("SELECT * FROM reading WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)
    check_wish  = db.execute("SELECT * FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    check_read  = db.execute("SELECT * FROM read WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session['user_id'], book_id=book_id)

    if len(check_read) != 0 or len(check_reading) != 0:
        message = "Already in read or reading lists!"
        return render_template("apology-modal.html", message=message)

    if len(check_wish) != 0:
        message = "Already in reading wishlist!"
        return render_template("apology-modal.html", message=message)

    confirm_result = book_client.get_id(book_id)
    return render_template("confirm-read-wish.html", row=confirm_result, _type=book_type)

@app.route("/add-read-wish", methods=["POST"])
@login_required
def add_read_wish():
    global book_id
    global book_type

    add = book_client.get_id(book_id)
    db.execute("INSERT INTO read_wish (user_id, book_id) VALUES (:user_id, :book_id)",
        user_id=session["user_id"], book_id=book_id)
    check_duplicate = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
    if len(check_duplicate) == 0:
        db.execute("INSERT INTO books VALUES (:book_id, :title, :authors, :publisher, :description, :smallimage, :mediumimage, :largeimage, :booktype)",
            book_id=book_id, title=add["title"], authors=add["authors"], publisher=add["publisher"], description=add["description"], smallimage=add["smallimage"], mediumimage=add["mediumimage"], largeimage=add["largeimage"], booktype=book_type )

    book_type = "type"
    book_id = "b"

    flash("Added sucessfully!")
    return redirect("/read-wish")

@app.route("/remove-read-wish", methods=["POST"])
@login_required
def remove_read_wish():
    global book_id
    book_id = request.form.get("remove")
    db.execute("DELETE FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
            user_id=session["user_id"], book_id=book_id)

    book_id = "b"

    flash("Removed sucessfully!")
    return redirect("/read-wish")

@app.route("/type-read-wish", methods=["POST"])
@login_required
def type_read_wish():
    global book_id
    book_id = request.form.get("typeChange")

    global book_type

    data = db.execute("SELECT * FROM books WHERE book_id = :book_id", book_id=book_id)
    book_type = data[0]['type']

    return render_template("type-read-wish.html", _type=book_type)

@app.route("/change-type-read-wish", methods=["POST"])
@login_required
def change_type_read_wish():
    global book_id
    global book_type
    book_type = request.form.get("type")

    db.execute("UPDATE books SET type = :new_type WHERE book_id = :book_id", new_type=book_type, book_id=book_id)

    book_type = "type"
    book_id = "b"

    flash("Type updated sucessfully!")
    return redirect("/read-wish")

@app.route("/Change2Reading", methods=["POST"])
@login_required
def change2reading_step1():
    global book_id
    book_id = request.form.get("readingchange")

    return render_template("change2reading.html")

@app.route("/change2readingAdd", methods=["POST"])
@login_required
def change2reading_stepAdd():
    global book_id
    rating = request.form.get('rating')

    db.execute("DELETE FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
    user_id=session["user_id"], book_id=book_id)
    db.execute("INSERT INTO reading (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
    user_id=session["user_id"], book_id=book_id, rating=rating)

    book_id = "b"

    flash("Moved to reading")
    return redirect("/read-wish")

@app.route("/Change2Read", methods=["POST"])
@login_required
def change2read_step1():
    global book_id
    book_id = request.form.get("readchange")

    return render_template("change2read.html")

@app.route("/change2readAdd", methods=["POST"])
@login_required
def change2read_stepAdd():
    global book_id
    rating = request.form.get('rating')

    db.execute("DELETE FROM read_wish WHERE user_id = :user_id AND book_id = :book_id",
        user_id=session["user_id"], book_id=book_id)
    db.execute("INSERT INTO read (user_id, book_id, rating) VALUES (:user_id, :book_id, :rating)",
        user_id=session["user_id"], book_id=book_id, rating=rating)

    book_id = "b"

    flash("Moved to read list")
    return redirect("/read-wish")

@app.route("/new-series", methods=["POST"])
@login_required
def new_series():
    global imdb_id
    imdb_id = request.form.get('new_series')

    data = db.execute("SELECT * FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
    user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("DELETE FROM watched WHERE user_id = :user_id AND imdb_id = :imdb_id",
    user_id=session["user_id"], imdb_id=imdb_id)
    db.execute("INSERT INTO watching (user_id, imdb_id, rating) VALUES (:user_id, :imdb_id, :rating)",
    user_id=session["user_id"], imdb_id=imdb_id, rating=data[0]['rating'])

    imdb_id = "tt"

    flash("Moved to watching")
    return redirect("/watched")

@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    db.execute("DELETE FROM watched WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM watching WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM watch_wish WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM read WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM reading WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM read_wish WHERE user_id = :user_id",
    user_id=session["user_id"])
    db.execute("DELETE FROM users WHERE id = :user_id",
    user_id=session["user_id"])

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Goodbye! Sorry to see you go!")
    return render_template("index.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

