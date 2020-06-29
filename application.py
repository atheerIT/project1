from sqlalchemy import create_engine
from flask_session import Session
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request, session, jsonify
import requests

app=Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"]= False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "hello"

# Set up database
engine = create_engine("postgres://cbgfiufiugsgld:f5f49d9548f4c3fb1f9d8360a4415b8172fe574dcffe889ed9e82859153451df@ec2-35-172-73-125.compute-1.amazonaws.com:5432/d3ap3dqmbg5aof")
db = scoped_session(sessionmaker(bind=engine))

#index function
@app.route("/")
def index():
    if "user" in session:
        user = db.execute("select * from users where id= :id", {"id": session.get("user")}).fetchone()
        return render_template("search.html", username=user.username, message="You are loged in as", title="please search for book by title, author, or ISBN")
    else:
        return render_template("index.html")

#Login Function
@app.route("/login", methods=["POST"])
def login():
    username=request.form.get("username")
    password=request.form.get("password")
    if db.execute("select * from users where username= :username and password= :password", {"username":username, "password":password}).rowcount == 0:
        return render_template("error.html", message="The username or password is not correct")
    user = db.execute("select * from users where username= :username and password= :password", {"username":username, "password":password}).fetchone()
    session["user"] = user.id
    return render_template("search.html", username=user.username, message="You are loged in as", title="please search for book by title, author, or ISBN")

#Registration Page
@app.route("/RegistrationPage")
def registerP():
    if "user" in session:
        user = db.execute("select * from users where id= :id", {"id": session.get("user")}).fetchone()
        return render_template("search.html", username=user.username, message="You are loged in as")
    else:
        return render_template("register.html")

#Registration Function
@app.route("/Register", methods=["POST"])
def register():
    username=request.form.get("username")
    password=request.form.get("password")
    if db.execute("select * from users where username= :username", {"username":username}).rowcount != 0 or username=="admin":
        return render_template("error.html", message="This username is already taken, please choose another one")
    db.execute("insert into users (username, password) values (:username, :password)", {"username":username, "password":password})
    db.commit()
    return render_template("success.html", username=username, message="You are registered as ")

#Search Function
@app.route("/search", methods=["POST"])
def search():
    searchW = request.form.get("searchW")
    if searchW == "":
        user = db.execute("select * from users where id= :id", {"id": session.get("user")}).fetchone()
        return render_template("search.html", title="please search for book by title, author, or ISBN", username=user.username, message="You are loged in as")
    searchW = "%"+searchW+"%"
    results = db.execute("select * from books where isbn like :searchW or title like :searchW or author like :searchW ", {"searchW":searchW}).fetchall()
    user = db.execute("select * from users where id= :id", {"id": session.get("user")}).fetchone()
    return render_template("search.html", results=results, title="Please try another word.", username=user.username, message="You are loged in as ")

#Book Page and Function
@app.route("/book/<isbn>", methods=["GET", "POST"])
def bookPage(isbn):
    res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":"W6g1C6QWV4oHf1GEqTps7Q", "isbns":isbn})
    if res.status_code !=200:
        return render_template("error.html", message=res)
    data=res.json()
    norate=data["books"][0]["work_ratings_count"]
    avrate=data["books"][0]["average_rating"]
    book=db.execute("select * from books where isbn = :isbn", {"isbn": isbn}).fetchone()
    reviews=db.execute("select review, rate, username from reviews JOIN users ON users.id = reviews.user_id where book_id = :isbn", {"isbn":isbn}).fetchall()
    if request.method =="POST":
        reviewForm = request.form.get("review")
        rate = int(request.form.get("rate_value"))
        if reviewForm == "" or rate==0:
            return render_template("error.html", message="please write a review and rate the book befor submiting")
        if db.execute("select * from reviews where user_id= :id", {"id": session.get("user")}).rowcount !=0:
            return render_template("error.html", message="You already reviewed this book.")
        book=db.execute("select * from books where isbn = :isbn", {"isbn": isbn}).fetchone()
        db.execute("insert into reviews (user_id, book_id, review, rate) values (:user_id, :book_id, :review, :rate)", {"user_id": session.get("user"), "book_id":isbn, "review":reviewForm, "rate":rate})
        db.commit()
        reviews=db.execute("select review, rate, username from reviews JOIN users ON users.id = reviews.user_id where book_id = :isbn", {"isbn":isbn}).fetchall()
    return render_template("bookP.html", book=book, reviews=reviews, norate=norate, avrate=avrate)

#Logout Function
@app.route("/logout")
def logout():
    session.pop("user", None)
    return render_template("index.html")

#API Function
@app.route("/api/<isbn>")
def book_api(isbn):
    book=db.execute("select * from books where isbn = :isbn", {"isbn":isbn}).fetchone()
    if book is None:
        return jsonify({"error": "The isbn is not found"}), 404
    review_count=db.execute("select * from reviews where book_id = :isbn", {"isbn":isbn}).rowcount
    rate_avrg=db.execute("select AVG(rate) as average from reviews where book_id = :isbn", {"isbn":isbn}).fetchone()
    average= round(float(rate_avrg['average']), 2)
    return jsonify({'title': book.title, 'author': book.author, 'year': book.year, 'isbn': book.isbn, 'review_count': review_count, 'average_score': average})
