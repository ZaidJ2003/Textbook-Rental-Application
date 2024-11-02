from src.models import db, users, Textbook, Cart, CartItem
from flask import abort, flash, session

class UserRepository:
    # check if a password meets all requirements
    def validate_input(self, first_name, last_name, username, phone_number, password):
        if len(first_name) <= 1:
            flash('First name must be greater than 1 character', category='error')
            return False
        elif len(last_name) <= 1:
            flash('Last name must be greater than 1 character', category='error')
            return False
        elif len(phone_number) != 10:
            flash('Invalid Phone Number', category='error')
            return False
        elif len(username) < 4:
            flash('Username name must be at least 4 characters', category='error')
            return False
        elif (len(password) < 6) or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or any(char.isspace() for char in password):
            flash('Password must contain at least 6 characters, a letter, a number, and no spaces', category='error')
            return False
        return True
    
    def add_user(self, first_name, last_name, username, email, phone_number, password, profile_picture):
        temp_user = users(first_name, last_name, username, email, phone_number, password, profile_picture)
        db.session.add(temp_user)
        db.session.commit()
        
    def remove_user(self, username):
        user = users.query.filter_by(username = username).first()
        if not user:
            abort(400)
        if user:
            db.session.delete(user)
            db.session.commit()

    def get_cart_num_items(self):
        curr_cart_items = CartItem.query.filter(CartItem.cart_id == session['cart']['cart_id']).all()
        total_items = 0
        if curr_cart_items is not None:
            for item in curr_cart_items:
                total_items += item.quantity
        return total_items

    def login_user(self, user):
        session['user'] = {
            'username' : user.username,
            'user_id' : user.user_id,
            'email' : user.email,
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'phone_number' : user.phone_number,
            'profile_picture' : user.profile_picture
        }

        if 'cart' not in session:
            session['cart'] = {}

        cart = Cart.query.filter(Cart.user_id == user.user_id).first()
        if cart:
            session['cart']['cart_id'] = cart.cart_id
            total_items = self.get_cart_num_items()
            session['cart']['quantity'] = total_items
        else:
            new_cart = Cart(user.user_id)
            db.session.add(new_cart)
            db.session.commit()
            session['cart']['cart_id'] = new_cart.cart_id
            session['cart']['quantity'] = 0

    def logout_user(self):
        del session['user']
        del session['cart']

    def is_logged_in(self):
        return 'user' in session
    
    def get_user_by_user_id(self, user_id):
        return users.query.filter_by(user_id=user_id).first()
    
    def get_user_by_username(self, username):
        return users.query.filter_by(username=username).first()
    
    def get_user_username(self):
        return session['user']['username']
    
    def get_user_user_id(self):
        return session['user']['user_id']
    
    def get_user_email(self):
        return session['user']['email']
    
    def get_user_first_name(self):
        return session['user']['first_name']
    
    def get_user_last_name(self):
        return session['user']['last_name']
    
    def get_user_profile_picture(self):
        return session['user']['profile_picture']
    
    def update_cart_quantity(self):
        if 'cart' in session:
            total_items = self.get_cart_num_items()
            session['cart']['quantity'] = total_items
            session.modified = True
    
    def clear_cart(self):
        if 'cart' in session and 'cart_id' in session['cart']:
            CartItem.query.filter(CartItem.cart_id == session['cart']['cart_id']).delete()
            db.session.commit()
            session['cart']['quantity'] = 0
            session.modified = True

# Singleton to be used in other modules
user_repository_singleton = UserRepository()
