# To run, must create virtual env and activate it, then run flask run

from flask import Flask, abort, redirect, render_template, request, url_for, flash, jsonify, session, blueprints

# Flask Initialization
app = Flask(__name__)

app.debug = True

@app.get('/')
def home():
    return render_template('index.html')

@app.get('/about')
def about():
    return render_template('about.html')

@app.get('/login')
def login():
    return render_template('login.html')

@app.get('/registration')
def register():
    return render_template('registration.html')

if __name__ == '__main__':
    app.run(debug=True)
