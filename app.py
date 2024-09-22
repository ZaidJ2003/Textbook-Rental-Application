# To run, must create virtual env and activate it, then run flask run

from flask import Flask, abort, redirect, render_template, request, url_for, flash, jsonify, session, blueprints
import os
from dotenv import load_dotenv
from src.repositories.models import db, users
from sqlalchemy import inspect

# Flask Initialization
app = Flask(__name__)

# App Secret Key
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', 'default')
app.debug = True

load_dotenv()
# If you have .env set up
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
# hardcoded if .env is not set up yet
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123@localhost:5432/textbook_application"
db.init_app(app)

#just some ai generated example books
textbooks = [
    {'title': 'Introduction to Python', 'description': 'A beginner\'s guide to Python programming.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$29.99'},
    {'title': 'Advanced Python Programming', 'description': 'Deep dive into advanced Python concepts.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$49.99'},
    {'title': 'Data Science with Python', 'description': 'Learn data science techniques using Python.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$39.99'},
    {'title': 'JavaScript: The Good Parts', 'description': 'A concise guide to the best features of JavaScript.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$34.99'},
    {'title': 'JavaScript: The Definitive Guide', 'description': 'An in-depth guide to JavaScript programming.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$44.99'},
    {'title': 'The Pragmatic Programmer', 'description': 'Tips and techniques for modern software development.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$42.99'},
    {'title': 'Clean Code', 'description': 'A handbook of agile software craftsmanship.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$37.99'},
    {'title': 'Design Patterns: Elements of Reusable Object-Oriented Software', 'description': 'Classic design patterns for object-oriented programming.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$49.99'},
    {'title': 'Introduction to Machine Learning', 'description': 'Basics of machine learning and practical applications.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$45.99'},
    {'title': 'Artificial Intelligence: A Modern Approach', 'description': 'Comprehensive overview of AI principles and techniques.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$59.99'},
    {'title': 'Algorithms Unlocked', 'description': 'A gentle introduction to algorithms and data structures.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$31.99'},
    {'title': 'The Art of Computer Programming', 'description': 'Foundational text on algorithms and programming techniques.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$69.99'},
    {'title': 'Computer Systems: A Programmer\'s Perspective', 'description': 'Insight into the underlying workings of computer systems.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$52.99'},
    {'title': 'Operating System Concepts', 'description': 'Essential concepts of modern operating systems.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$46.99'},
    {'title': 'Database System Concepts', 'description': 'Comprehensive guide to database systems and their use.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$48.99'},
    {'title': 'Computer Networking: A Top-Down Approach', 'description': 'Introduction to networking concepts from a top-down perspective.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$41.99'},
    {'title': 'Introduction to the Theory of Computation', 'description': 'Foundational concepts in computational theory.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$39.99'},
    {'title': 'Elements of Programming Interviews', 'description': 'Solutions to challenging programming interview questions.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$36.99'},
    {'title': 'Eloquent JavaScript', 'description': 'A modern introduction to JavaScript programming.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$29.99'},
    {'title': 'Python for Data Analysis', 'description': 'Using Python for analyzing and visualizing data.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$32.99'},
    {'title': 'Learning SQL', 'description': 'An introduction to SQL and database querying.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$27.99'},
    {'title': 'Web Design with HTML, CSS, JavaScript and jQuery Set', 'description': 'Comprehensive guide to web design and development.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$55.99'},
    {'title': 'React Up & Running', 'description': 'Hands-on guide to building modern web applications with React.', 'image_url': '/static/images/bookborrowlogo.jpg', 'price': '$39.99'}
]

@app.get('/')
def home():
    return render_template('index.html')

@app.get('/search')
def search():
    query = request.args.get('search_query', '')
    
    #whenever we add a database this is where we will query it and you will return the array of textbooks to filtered_textbooks
    #for now it doesn't query anything and just shows all the textbooks along with whatever you put in the search bar
    filtered_textbooks = textbooks

    return render_template('search_results.html', query=query, textbooks=filtered_textbooks)


@app.get('/about')
def about():
    return render_template('about.html')

@app.get('/login')
def login():
    #test data
    # user = users("Zaid", "test", "test@test.com", "temp", "123")
    # db.session.add(user)
    # db.session.commit()
    return render_template('login.html')

@app.get('/register')
def register():
    return render_template('register.html')

@app.get('/book')
def book():

    #just brings in the data from the search page to display it on the book page. Could also directly get the data from the database using a primary key but this is temporary.
    title = request.args.get('title', '')
    description = request.args.get('description', '')
    image_url = request.args.get('image_url', '')
    price = request.args.get('price', '')


    return render_template('book.html', title=title, description=description, image_url=image_url, price=price)

if __name__ == '__main__':
    app.run(debug=True)
