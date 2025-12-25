from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/bookexchange")
db = client['book_exchange_db']
users_collection = db['users']
books_collection = db['books']
messages_collection = db['messages']  # Chat messages

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility function for unread messages
@app.context_processor
def utility_processor():
    def get_unread_count(book_id, other_user_id):
        return messages_collection.count_documents({
            "book_id": book_id,
            "from_user": other_user_id,
            "to_user": session['user'],
            "read": False
        })
    return dict(get_unread_count=get_unread_count)

# Home page
@app.route('/')
def index():
    books = list(books_collection.find())
    for book in books:
        book['_id'] = str(book['_id'])
        book['owner_id'] = str(book['owner_id'])
        if 'image_url' not in book:
            book['image_url'] = ''
    return render_template('index.html', books=books)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if users_collection.find_one({"username": username}):
            return "User already exists!"
        users_collection.insert_one({"username": username, "password": password, "role": role})
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')
        user = users_collection.find_one({"username": username, "password": password, "role": role})
        if user:
            session['user'] = str(user['_id'])
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

# User dashboard
@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))

    all_books = list(books_collection.find())
    for book in all_books:
        book['_id'] = str(book['_id'])
        book['owner_id'] = str(book['owner_id'])
        if 'image_url' not in book:
            book['image_url'] = ''

    # Messages for books owned by user
    incoming_chats = []
    user_books_ids = [book['_id'] for book in all_books if book['owner_id'] == session['user']]

    for book_id in user_books_ids:
        senders = messages_collection.distinct("from_user", {"book_id": book_id, "to_user": session['user']})
        for sender_id in senders:
            incoming_chats.append({
                "book_id": book_id,
                "other_user_id": sender_id
            })

    return render_template('user_dashboard.html', books=all_books, incoming_chats=incoming_chats)

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    all_books = list(books_collection.find())
    for book in all_books:
        book['_id'] = str(book['_id'])
        book['owner_id'] = str(book['owner_id'])
        if 'image_url' not in book:
            book['image_url'] = ''

    all_messages = list(messages_collection.find().sort("timestamp", -1))

    return render_template('admin_dashboard.html', books=all_books, messages=all_messages)

# Add book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        image = request.files.get('image')
        image_url = ''
        if image and image.filename != '':
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            image_url = '/' + image_path.replace("\\", "/")
        books_collection.insert_one({
            "title": title,
            "author": author,
            "owner_id": session['user'],
            "image_url": image_url
        })
        return redirect(url_for('user_dashboard'))
    return render_template('add_book.html')

# Delete book
@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    book = books_collection.find_one({"_id": ObjectId(book_id)})
    if book:
        if session.get('role') == 'admin' or book['owner_id'] == session['user']:
            books_collection.delete_one({"_id": ObjectId(book_id)})
    return redirect(request.referrer)

# Chat route
@app.route('/chat/<book_id>/<other_user_id>', methods=['GET', 'POST'])
def chat(book_id, other_user_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        msg = request.form['message']
        if msg.strip() != "":
            messages_collection.insert_one({
                "book_id": book_id,
                "from_user": session['user'],
                "to_user": other_user_id,
                "message": msg,
                "timestamp": datetime.now(),
                "read": False
            })
        return redirect(request.referrer)

    # Mark incoming messages as read
    messages_collection.update_many(
        {"book_id": book_id, "from_user": other_user_id, "to_user": session['user'], "read": False},
        {"$set": {"read": True}}
    )

    msgs = list(messages_collection.find({
        "book_id": book_id,
        "$or": [
            {"from_user": session['user'], "to_user": other_user_id},
            {"from_user": other_user_id, "to_user": session['user']}
        ]
    }).sort("timestamp", 1))

    return render_template('chat.html', messages=msgs, other_user_id=other_user_id, book_id=book_id)

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
