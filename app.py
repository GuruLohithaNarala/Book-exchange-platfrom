from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)

# ===============================
# SECRET KEY (use env in prod)
# ===============================
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

# ===============================
# MONGODB CONNECTION (Atlas)
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["book_exchange_db"]
users_collection = db["users"]
books_collection = db["books"]
messages_collection = db["messages"]

# ===============================
# UPLOAD CONFIG
# ===============================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ===============================
# UNREAD MESSAGE COUNT
# ===============================
@app.context_processor
def utility_processor():
    def get_unread_count(book_id, other_user_id):
        if "user" not in session:
            return 0
        return messages_collection.count_documents({
            "book_id": book_id,
            "from_user": other_user_id,
            "to_user": session["user"],
            "read": False
        })
    return dict(get_unread_count=get_unread_count)

# ===============================
# HOME
# ===============================
@app.route("/")
def index():
    books = list(books_collection.find())
    for book in books:
        book["_id"] = str(book["_id"])
        book["owner_id"] = str(book["owner_id"])
        book.setdefault("image_url", "")
    return render_template("index.html", books=books)

# ===============================
# REGISTER
# ===============================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if users_collection.find_one({"username": username}):
            return "User already exists!"

        users_collection.insert_one({
            "username": username,
            "password": password,  # ⚠️ hash in production
            "role": role
        })
        return redirect(url_for("login"))

    return render_template("register.html")

# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        user = users_collection.find_one({
            "username": username,
            "password": password,
            "role": role
        })

        if user:
            session["user"] = str(user["_id"])
            session["role"] = user["role"]

            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))

        return "Invalid credentials"

    return render_template("login.html")

# ===============================
# USER DASHBOARD
# ===============================
@app.route("/user_dashboard")
def user_dashboard():
    if "user" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    books = list(books_collection.find())
    for book in books:
        book["_id"] = str(book["_id"])
        book["owner_id"] = str(book["owner_id"])
        book.setdefault("image_url", "")

    incoming_chats = []
    user_books = [b["_id"] for b in books if b["owner_id"] == session["user"]]

    for book_id in user_books:
        senders = messages_collection.distinct(
            "from_user",
            {"book_id": book_id, "to_user": session["user"]}
        )
        for sender in senders:
            incoming_chats.append({
                "book_id": book_id,
                "other_user_id": sender
            })

    return render_template(
        "user_dashboard.html",
        books=books,
        incoming_chats=incoming_chats
    )

# ===============================
# ADMIN DASHBOARD
# ===============================
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    books = list(books_collection.find())
    for book in books:
        book["_id"] = str(book["_id"])
        book["owner_id"] = str(book["owner_id"])
        book.setdefault("image_url", "")

    messages = list(messages_collection.find().sort("timestamp", -1))
    return render_template(
        "admin_dashboard.html",
        books=books,
        messages=messages
    )

# ===============================
# ADD BOOK
# ===============================
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        image = request.files.get("image")

        image_url = ""
        if image and image.filename:
            path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(path)
            image_url = "/" + path.replace("\\", "/")

        books_collection.insert_one({
            "title": title,
            "author": author,
            "owner_id": session["user"],
            "image_url": image_url
        })

        return redirect(url_for("user_dashboard"))

    return render_template("add_book.html")

# ===============================
# DELETE BOOK
# ===============================
@app.route("/delete_book/<book_id>", methods=["POST"])
def delete_book(book_id):
    if "user" not in session:
        return redirect(url_for("login"))

    book = books_collection.find_one({"_id": ObjectId(book_id)})
    if book and (session["role"] == "admin" or book["owner_id"] == session["user"]):
        books_collection.delete_one({"_id": ObjectId(book_id)})

    return redirect(request.referrer)

# ===============================
# CHAT
# ===============================
@app.route("/chat/<book_id>/<other_user_id>", methods=["GET", "POST"])
def chat(book_id, other_user_id):
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        msg = request.form["message"].strip()
        if msg:
            messages_collection.insert_one({
                "book_id": book_id,
                "from_user": session["user"],
                "to_user": other_user_id,
                "message": msg,
                "timestamp": datetime.utcnow(),
                "read": False
            })
        return redirect(request.referrer)

    messages_collection.update_many(
        {
            "book_id": book_id,
            "from_user": other_user_id,
            "to_user": session["user"],
            "read": False
        },
        {"$set": {"read": True}}
    )

    msgs = list(messages_collection.find({
        "book_id": book_id,
        "$or": [
            {"from_user": session["user"], "to_user": other_user_id},
            {"from_user": other_user_id, "to_user": session["user"]}
        ]
    }).sort("timestamp", 1))

    return render_template(
        "chat.html",
        messages=msgs,
        other_user_id=other_user_id,
        book_id=book_id
    )

# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ===============================
# RUN LOCAL
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
