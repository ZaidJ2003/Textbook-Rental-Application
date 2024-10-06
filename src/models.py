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

class Cart(db.Model):
        __tablename__ = 'carts' 

        cart_id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

        def __init__(self, user_id):
                self.user_id = user_id

# Cart items table
class CartItem(db.Model):
        __tablename__ = 'cart_items'

        item_id = db.Column(db.Integer, primary_key=True)
        cart_id = db.Column(db.Integer, db.ForeignKey('carts.cart_id'), nullable=False)
        textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.textbook_id'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False)

        def __init__(self, cart_id, textbook_id, quantity):
                self.cart_id = cart_id
                self.textbook_id = textbook_id
                self.quantity = quantity