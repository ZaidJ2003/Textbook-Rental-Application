from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from sqlalchemy.sql import func
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os
from uuid import uuid4

db = SQLAlchemy()

# User table
class users(db.Model, UserMixin):
        __tablename__ = 'users'
        user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        first_name = db.Column(db.String(255), nullable=False)
        last_name = db.Column(db.String(255), nullable=False)
        email = db.Column(db.String(255), nullable=False, unique=True)
        username = db.Column(db.String(255), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False)
        registration_date = db.Column(db.DateTime, nullable=True, default=func.now())
        profile_picture = db.Column(db.String(255), nullable=True)
        phone_number = db.Column(db.String(20), nullable=False)

        def __init__(self, first_name, last_name, email, phone_number, username, password, profile_picture):
                self.first_name = first_name
                self.last_name = last_name
                self.email = email
                self.username = username
                self.password = password
                self.profile_picture = profile_picture
                self.phone_number = phone_number
        
        def get_reset_token(self, expires_sec=900):
                # must have app_secret key variable in env file
                app_secret_key = os.getenv('APP_SECRET_KEY')
                if app_secret_key:
                        s = Serializer(app_secret_key)
                        token = s.dumps({'user_id' : str(self.user_id)})
                        if isinstance(token, bytes):
                                token = token.decode()
                        return token
                return None
        
        @staticmethod
        def verify_reset_token(token):
                # must have app_secret key variable in env file
                app_secret_key = os.getenv('APP_SECRET_KEY')
                if app_secret_key:
                        s = Serializer(app_secret_key)
                        try:
                                user_id = s.loads(token)['user_id']
                        except:
                                return None
                        return users.query.get(user_id)
                return None

class UnverifiedUsers(db.Model):
        __tablename__ = 'unverified_users'
        unverified_user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        first_name = db.Column(db.String(255), nullable=False)
        last_name = db.Column(db.String(255), nullable=False)
        email = db.Column(db.String(255), nullable=False, unique=True)
        username = db.Column(db.String(255), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False)
        registration_date = db.Column(db.DateTime, nullable=True, default=func.now())
        profile_picture = db.Column(db.String(255), nullable=True)
        phone_number = db.Column(db.String(20), nullable=False)

        def __init__(self, first_name, last_name, email, phone_number, username, password, profile_picture):
                self.first_name = first_name
                self.last_name = last_name
                self.email = email
                self.username = username
                self.password = password
                self.profile_picture = profile_picture
                self.phone_number = phone_number

# Textbook table
class Textbook(db.Model):
        __tablename__ = 'textbooks'
        textbook_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        owners_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        title = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, nullable=False)
        image_url = db.Column(db.String(255))
        price = db.Column(db.Numeric(10, 2), nullable=False)
        created_at = db.Column(db.DateTime, default=func.now())

        owner = db.relationship('users', foreign_keys=[owners_user_id], backref='textbooks')

# Cart table
class Cart(db.Model):
        __tablename__ = 'carts'
        cart_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)

        def __init__(self, user_id):
                self.user_id = user_id

# Cart items table
class CartItem(db.Model):
        __tablename__ = 'cart_items'
        item_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey('carts.cart_id'), nullable=False)
        textbook_id = db.Column(UUID(as_uuid=True), db.ForeignKey('textbooks.textbook_id'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False)

        def __init__(self, cart_id, textbook_id, quantity):
                self.cart_id = cart_id
                self.textbook_id = textbook_id
                self.quantity = quantity

# Conversations table
class Conversations(db.Model):
        __tablename__ = 'conversations'
        conversation_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        sender_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        receiver_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        textbook_id = db.Column(UUID(as_uuid=True), db.ForeignKey('textbooks.textbook_id'), nullable=False)
        meetup_location = db.Column(db.String(255), nullable=True)

        messages = db.relationship('Messages', backref='conversation', lazy=True)

        sender = db.relationship('users', foreign_keys=[sender_user_id], backref='sent_conversations')

        receiver = db.relationship('users', foreign_keys=[receiver_user_id], backref='received_conversations')

        textbook = db.relationship('Textbook', foreign_keys=[textbook_id])

        def __init__(self, sender_user_id, receiver_user_id, textbook_id, meetup_location=None):
                self.sender_user_id = sender_user_id
                self.receiver_user_id = receiver_user_id
                self.textbook_id = textbook_id
                self.meetup_location = meetup_location

# Messages table
class Messages(db.Model):
        __tablename__ = 'messages'
        message_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        conversation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('conversations.conversation_id'), nullable=False)
        message_text = db.Column(db.String(255), nullable=False)
        created_at = db.Column(db.DateTime, nullable=False, default=func.now())

        def __init__(self, user_id, conversation_id, message_text):
                self.user_id = user_id
                self.conversation_id = conversation_id
                self.message_text = message_text

# Verification Codes table
class VerificationCodes(db.Model):
        __tablename__ = 'verification_codes'
        code_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        verification_code = db.Column(db.String(255), nullable=False)
        expiration_timestamp = db.Column(db.DateTime, nullable=False)
        is_used = db.Column(db.Boolean, default=False)

        def __init__(self, user_id, verification_code, expiration_date):
                self.user_id = user_id
                self.verification_code = verification_code
                self.expiration_timestamp = expiration_date

# Order table
class Order(db.Model):
        __tablename__ = 'orders'
        order_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
        status = db.Column(db.String(10), default='pending')
        price = db.Column(db.Numeric(10, 2), nullable=False)
        order_date = db.Column(db.DateTime, nullable=False, default=func.now())

        orderItems = db.relationship('OrderItem', back_populates='order', lazy=True)

        def __init__(self, user_id, price, status='pending', order_id = None):
                self.order_id = order_id or uuid4()
                self.user_id = user_id
                self.status = status
                self.price = price

# Cart items table
class OrderItem(db.Model):
        __tablename__ = 'order_items'
        item_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.order_id'), nullable=False)
        textbook_id = db.Column(UUID(as_uuid=True), db.ForeignKey('textbooks.textbook_id'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False)

        order = db.relationship('Order', back_populates='orderItems', lazy=True)
        textbook = db.relationship('Textbook', foreign_keys=[textbook_id], lazy=True)

        def __init__(self, order_id, textbook_id, quantity):
                self.order_id = order_id
                self.textbook_id = textbook_id
                self.quantity = quantity