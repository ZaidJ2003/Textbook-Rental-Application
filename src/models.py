from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin

db = SQLAlchemy()

#User table
class users(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(255), nullable = False)
    last_name = db.Column(db.String(255), nullable = False)
    email = db.Column(db.String(255), nullable = False, unique = True)
    username = db.Column(db.String(255), nullable = False, unique = True)
    password = db.Column(db.String(255), nullable = False)
    registration_date = db.Column(db.DateTime, nullable=True, default=func.now())
    profile_picture = db.Column(db.String(255), nullable = True)

    def __init__(self, first_name, last_name, email, username, password, profile_picture):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.profile_picture = profile_picture
#Textbook table
class Textbook(db.Model):
    __tablename__ = 'textbooks'

    textbook_id = db.Column(db.Integer, primary_key=True)
    owners_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())