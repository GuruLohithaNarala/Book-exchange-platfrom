📚 Book Exchange Web Application

A full-featured Book Exchange Website that allows users to register, log in, browse available books, upload books for exchange, and communicate with other users.
The application is built using Flask, MongoDB, and HTML/CSS, and runs as a traditional server-rendered web application.

🌐 Project Overview

The Book Exchange platform enables users to exchange books instead of purchasing new ones.
Users can upload book details with images, browse books shared by others, and interact through a simple messaging system.

✨ Functionalities
👤 User Management

User registration with username and password

Secure login authentication

Separate dashboards for users and admin

Session-based access control

Logout functionality

📖 Book Management

View all available books on the homepage

Add new books with:

Book title

Author name

Book cover image

Uploaded images are stored in static/uploads

Books displayed in a card-style layout

💬 Messaging / Chat

Users can send messages to other users

Chat interface available through the chat page

Messages stored in the database

🧑‍💼 Admin Features

Admin dashboard

View all users and uploaded books

Manage platform content

🎨 User Interface

Responsive and visually appealing UI

Navigation bar with Login / Register options

Background image and styled book cards

Clean, user-friendly design

🛠 Tech Stack
Backend

Python

Flask

MongoDB

Flask-PyMongo

Frontend

HTML

CSS

Jinja2 Templates

Database

MongoDB (Local)

📁 Project Structure
BOOK_EXCHANGE_APP/
├── static/
│   └── uploads/              # Uploaded book images
│
├── templates/
│   ├── index.html            # Homepage (Available Books)
│   ├── login.html            # Login page
│   ├── register.html         # Register page
│   ├── add_book.html         # Add book page
│   ├── user_dashboard.html   # User dashboard
│   ├── admin_dashboard.html  # Admin dashboard
│   └── chat.html             # Messaging page
│
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
└── README.md

⚙️ Installation & Setup
1️⃣ Prerequisites

Ensure you have:

Python 3.8 or above

MongoDB Community Edition

pip (Python package manager)

2️⃣ Start MongoDB
mongod


MongoDB runs on:

mongodb://localhost:27017

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run the Application
python app.py

5️⃣ Access the Website

Open your browser and go to:

http://127.0.0.1:5000/

🧪 Testing the Application

Register a new user

Log in using credentials

Add a book with an image

View books on the homepage

Send messages using the chat feature

🔐 Security Features

Password hashing using Werkzeug

Session-based authentication

Protected routes for logged-in users only

📌 Future Enhancements

Book exchange request & approval system

Email notifications

Advanced search & filters

JWT-based authentication

Cloud deployment

Rating & review system

🎓 Academic Relevance

This project is suitable for:

Mini Project

Final Year Project

Web Development Course

Full Stack Development Demonstration

📄 License

This project is developed for educational purposes only.

🙌 Acknowledgements

Flask Documentation

MongoDB Documentation

Open-source UI inspiration
