import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# login page
@app.route("/")
def index():
    return render_template("index.html")

# logout page
@app.route("/logout")
def logout():
    # session["user_id"] = ""
    # session["book_res"] = ""
    # session["book_id"] = ""
    session.pop('user_id', None)
    return render_template("index.html")


# home page
@app.route("/home")
def home():
    if 'user_id' in session:
        return render_template("home.html", name=session["name"],result_head="")
    
    return render_template("index.html", message="Sorry! You are yet to login. Thanks", )

# signup page
@app.route("/signup")
def signup():
    return render_template("signup.html")

# login api
@app.route("/login", methods=["POST"])
def login():
    user_name = request.form.get("user_name")
    password = request.form.get("password")
    
    user_res = db.execute("SELECT * FROM users WHERE user_name = :user_name",
                              {"user_name": user_name}).fetchone()
    session["user_id"] = user_res.id
    session["name"] = user_res.user_name
    
    if db.execute("SELECT id FROM users WHERE user_name = :user_name",
                  {"user_name": user_name}).rowcount == 1:
        return render_template("home.html", name=user_name, result_head="")
    
    return render_template("index.html", message="Sorry! You are yet to signup. Thanks")
        
# registeration api
@app.route("/register", methods=["POST"])
def register():
    user_name = request.form.get("user_name")
    password = request.form.get("password")

    # Check if username exists
    if db.execute("SELECT id FROM users WHERE user_name = :user_name",
                  {"user_name": user_name}).rowcount != 0:
        return render_template("signup.html", message="Sorry! User already exists.")

    # Insert user in database
    db.execute("INSERT INTO users (user_name, password) VALUES (:user_name, :password)",
               {"user_name": user_name, "password": password})

    db.commit()
    return render_template("home.html", name=user_name, result_head="")


@app.route("/search", methods=["POST"])
def search():
    """Lookup user query in database"""

    # TO DO: refine with wildcard to curb superfluous results
    
    # logged in users can search for books
    # via 'isbn', 'author', or 'title'
    query = request.form.get("search")
    if not query:
        return render_template("home.html", result=0, name=session["name"],result_head="Results")
    
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
    return render_template("home.html", result=res, name=session["name"], result_head="Results")   

@app.route("/book/<book_isbn>")
def book(book_isbn):
    """Return book details and reviews"""

    if len(book_isbn) == 10 and book_isbn.isdigit():
        # Get book details
        book_res = db.execute("SELECT * FROM books WHERE isbn = :book_isbn",
                              {"book_isbn": book_isbn}).fetchone()
        session["book_res"] = book_res
        session["book_id"] = book_res.id
        session["book_isbn"] = book_res.isbn

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "bgh2LQUdiQnnDznXzFMbg", "isbns": book_isbn})
        resp = res.json()
        # return resp


        # Get reviews
        review_res = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",
                         {"book_id": session["book_id"]}).fetchall()
        session["review_res"] = review_res

        return render_template("book.html", book=book_res, reviews=review_res, count=resp["books"][0],name=session["name"])

    return render_template("book.html", message="Oops, something went wrong.",name=session["name"])

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
        return render_template("book.html", message="Oops something went wrong",name=session["name"])

    db.commit()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "bgh2LQUdiQnnDznXzFMbg", "isbns": session["book_isbn"]})
    resp = res.json()

    return render_template("book.html", book=session["book_res"], reviews=session["review_res"],name=session["name"],count=resp["books"][0]) 
  