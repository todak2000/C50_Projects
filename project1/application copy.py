import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Goodreads API
#api_key = os.getenv("APP_API_KEY")


# DADTABASE URL
postgres://oevdseguxheada:e7474bcf173355f6444badb5bfe2c78e65ba98d627b5863068bd7939b8c0415d@ec2-50-19-114-27.compute-1.amazonaws.com:5432/d1ecvl3ru9huu5


def create_app():
    app = Flask(__name__)
    Bootstrap(app)
 
    return app
# Check for environment variable
if not os.getenv("DATABASE_URL_P1"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL_P1"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    """Main page"""
    
    return render_template("index.html")

#  Log-in and Registration Routes
@app.route("/registration")
def registration():
    """Registration page"""
    
    return render_template("registration.html")
    
@app.route("/register", methods=["POST"])
def register():
    """Register a user"""

    user_name = request.form.get("user_name")
    password = request.form.get("password")

    # Check if username exists
    if db.execute("SELECT id FROM users WHERE user_name = :user_name",
                  {"user_name": user_name}).rowcount != 0:
        return render_template("error.html", message="Username already exists.")

    # Insert user in database
    db.execute("INSERT INTO users (user_name, password) VALUES (:user_name, :password)",
               {"user_name": user_name, "password": password})

    db.commit()
    return render_template("success.html")

@app.route("/search", methods=["POST"])
def search():
    """Present user with book lookup after logging in"""

    # TO DO: implement better and safer solution!
    user_name = request.form.get("user_name")
    password = request.form.get("password")

    if not session.get("user_name"):
        session["user_id"] = ""

    user_res = db.execute("SELECT * FROM users WHERE user_name = :user_name",
                              {"user_name": user_name}).fetchone()
    session["user_id"] = user_res.id
    
    if db.execute("SELECT password FROM users WHERE user_name = :user_name",
                               {"user_name": user_name}).fetchone()[0] == password:
        return render_template("search.html")

    return render_template("error.html", message="Incorrect username or password.")

# Content Routes
@app.route("/lookup", methods=["POST"])
def lookup():
    """Lookup user query in database"""

    # TO DO: refine with wildcard to curb superfluous results
    
    # logged in users can search for books
    # via 'isbn', 'author', or 'title'
    query = request.form.get("search")
    if not query:
        return render_template("search.html", result=0)
    
    # query 'isbn'
    if query.isdigit():
        res = db.execute("SELECT * FROM books WHERE isbn LIKE :query",
                         {"query": f"{query}%"}).fetchall()
    else:
        # query 'author'
        res = db.execute("SELECT * FROM books WHERE author LIKE :query",
                          {"query": f"{query}%"}).fetchall()
        # If no result from author, query 'title'
        if len(res) == 0:
            res = db.execute("SELECT * FROM books WHERE title LIKE :query",
                             {"query": f"{query}%"}).fetchall()
    if len(res) == 0:
        res = 0
    return render_template("search.html", result=res)

@app.route("/book/<book_isbn>")
def book(book_isbn):
    """Return book details and reviews"""

    if len(book_isbn) == 10 and book_isbn.isdigit():
        # Get book details
        book_res = db.execute("SELECT * FROM books WHERE isbn = :book_isbn",
                              {"book_isbn": book_isbn}).fetchone()
        session["book_res"] = book_res
        session["book_id"] = book_res.id

        # Get reviews
        review_res = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",
                         {"book_id": session["book_id"]}).fetchall()
        session["review_res"] = review_res

        return render_template("book.html", book=book_res, reviews=review_res)

    return render_template("book.html", message="Oops, something went wrong.")

# to implement
@app.route("/post_review", methods=["POST"])
def post_review():
    """"""

    review = request.form.get("review")
    score = request.form.get("score")

    # Check if user already posted a review for this book
    # TO IMPLEMENT
    
    try:
        db.execute("INSERT INTO reviews (text, score, user_id, book_id) VALUES (:text, :score, :user_id, :book_id)",
                   {"text": review,
                    "score": score,
                    "user_id": session["user_id"],
                    "book_id": session["book_id"]
                   })    
    except:
        return render_template("error.html", message="Oops something went wrong")

    db.commit()
    return render_template("book.html", book=session["book_res"], reviews=session["review_res"])