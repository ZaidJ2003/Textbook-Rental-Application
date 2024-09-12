# To run, must create virtual env and activate it, then run flask run

from flask import Flask, abort, redirect, render_template, request, url_for, flash, jsonify, session, blueprints

# Flask Initialization
app = Flask(__name__)

app.debug = True

@app.get('/')
def index():
    return render_template('index.html')