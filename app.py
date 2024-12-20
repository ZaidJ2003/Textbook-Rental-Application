# To run, must create virtual env and activate it, then run flask run
from decimal import Decimal
import random
from uuid import uuid4
from flask import Flask, abort, redirect, render_template, request, url_for, flash, jsonify, session, blueprints, render_template_string
import os
from dotenv import load_dotenv
from src.models import db, users, Textbook, Cart, CartItem, Messages, Conversations, VerificationCodes, UnverifiedUsers, Order, OrderItem, Rating, Meetup
from sqlalchemy import or_, func, and_
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from src.repositories.user_repository import user_repository_singleton
import googlemaps
import stripe
from flask import g
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import ssl
from datetime import datetime, timedelta
import base64

#bcrypt, os, dotenv might be helpful (delete comment if not needed)
load_dotenv()
# Flask Initialization
app = Flask(__name__)
#gmaps key
gmaps = googlemaps.Client(key='AIzaSyDUNewuSDlRLem-I3kcBnvU6467VleNicM')

# App Secret Key
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', 'default')

app.config['UPLOAD_FOLDER'] = 'static/images'
app.debug = True

# If you have .env set up
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
# hardcoded if .env is not set up yet
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123@localhost:5432/textbook_application"
db.init_app(app)

# Hashing algo
bcrypt = Bcrypt(app)

#-------------------------Sets the allowed extensions for image uploads-------------------------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#-------------------------Sets the allowed extensions for image uploads-------------------------

# Global test api key for Stripe
stripe.api_key = 'sk_test_51Q6zr6BsbRXEeqR8BeQBHg39OmzSwbOOw3YHFCKV42pl0InBUCq2zOIwjMXgyzCxDEYvuziLlLl8ayjZKnBPPlPm00EtEGae67'

# Twilio (library for sending codes through phone) Credentials - Turned out to not be free so differing to email for now
TWILIO_ACCOUNT_SID = 'AC8040bd31dbca9bf5dfdadac60b3872ab'
TWILIO_AUTH_TOKEN = '364085e68f48b5b0508f5125dd6a6e0c'
TWILIO_PHONE_NUMBER = '+19546211760'
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Email API Key (will hide when deployed) and disabling SSL verification as emails wont send with verification required on
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

not_logged_in_message = 'You must be logged in to access this page'

ssl._create_default_https_context = ssl._create_unverified_context

@app.template_filter('format_date')
def format_date(value, format='%B %d, %Y'):
    if value is None:
        return ""
    return value.strftime(format)

def send_verification_email(email, code):
    if not email:
        abort(403) 
    
    message = Mail(
        from_email='bookborrow763@gmail.com',
        to_emails=email,
        subject='BookBorrow registration code',
        html_content=f'''
        <p>Enter the 6-digit code below to verify your identity.</p>
        <h3>{code}</h3>
        <p>If you did not make this request, please ignore this email.</p>
        '''
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True 
    except Exception as e:
        print(f'Error sending email: {e}')  
        return False 

def generate_and_send_code(user_id, email):
    current_user = UnverifiedUsers.query.filter(UnverifiedUsers.unverified_user_id == user_id).first()
    if current_user:
        existing_codes = VerificationCodes.query.filter(VerificationCodes.user_id == user_id).all()
        for code in existing_codes:
            db.session.delete(code)
        db.session.commit()

        code = str(random.randint(100000, 999999))
        verification_code = VerificationCodes(user_id, code, datetime.now() + timedelta(minutes=15)) 
        db.session.add(verification_code)
        db.session.commit()

        if send_verification_email(email, code):
            return verification_code.code_id
    return None

@app.get('/')
def home():
    if request.args.get('success') == "true":
        user_repository_singleton.add_delivery_order()
        user_repository_singleton.clear_cart()
        flash("Transaction successful! Order is out for delivery.", category="success")
    return render_template('index.html')

@app.get('/deleteAccount')
def deleteAccount():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')        
        return redirect(url_for('login'))
    
    user = db.session.query(users).filter(users.user_id == session['user']['user_id']).first()

    if user:
        user_repository_singleton.logout_user()

        cart = Cart.query.filter_by(user_id=user.user_id).first()
        if cart:
            CartItem.query.filter_by(cart_id=cart.cart_id).delete()
            db.session.delete(cart)

        conversations = Conversations.query.filter((Conversations.sender_user_id == user.user_id) |
                                                    (Conversations.receiver_user_id == user.user_id)).all()
        
        if conversations:
            for conversation in conversations:
                Messages.query.filter_by(conversation_id=conversation.conversation_id).delete()
                db.session.delete(conversation)

        textbooks = Textbook.query.filter_by(owners_user_id = user.user_id).all()

        for textbook in textbooks:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], textbook.image_url.split('/')[-1])
            if os.path.exists(image_path):           
                os.remove(image_path)


        if user.profile_picture != "/static/images/defaultPFP.png":
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_picture.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)

        Textbook.query.filter_by(owners_user_id=user.user_id).delete()

        db.session.delete(user)
        db.session.commit()

        session.clear()
        flash("Your account and all associated data have been successfully deleted.", category='success')
        return render_template('index.html')
    else:
        flash("User not found.", category='error')
        return redirect(url_for('profile'))


@app.get('/addDeleteTextbook')
def addDeleteTextbook():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')        
        return redirect(url_for('login'))
    
    filtered_textbooks = db.session.query(Textbook).filter(                    #creates a list of textbooks the user owns/uploaded
        or_(
            Textbook.owners_user_id == session['user']['user_id']
        )
    ).all()

    return render_template('addDeleteTextbook.html',textbooks=filtered_textbooks)

@app.route('/del_textbook', methods=['GET', 'POST'])
def del_textbook():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    textbook_id = request.args.get('textbook_id')    

    cart_items_to_delete = db.session.query(CartItem).filter(CartItem.textbook_id == textbook_id).all()
    for item in cart_items_to_delete:
        db.session.delete(item)
    
    #gets textbook_id and finds the textbook that matches that id in the database
    textbook = db.session.query(Textbook).filter(Textbook.textbook_id == textbook_id).first()
    if textbook is None:
        return "Textbook not found", 404

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], textbook.image_url.split('/')[-1]) #stores the image path before deletion
    db.session.delete(textbook)
    db.session.commit()

    if os.path.exists(image_path):             #removes the image
        os.remove(image_path)
    flash("Textbook deleted successfully", category='success')   
    return redirect(url_for('addDeleteTextbook'))

@app.route('/add_textbook', methods=['GET', 'POST'])
def add_textbook():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')  # makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')  # gets info from the form and the current user's id
        price = request.form.get('price')
        owners_user_id = session['user']['user_id']
        cropped_image_data_url = request.form.get('cropped_image')

#--------------------------------turn the base64 cropped image string and converts it to a png to be stored in static/images, new method follows the same image naming convention as the old one------------------
        if cropped_image_data_url:
            image_data = cropped_image_data_url.split(",")[1]
            image_bytes = base64.b64decode(image_data)

            new_textbook = Textbook(title=title, description=description, image_url="", price=price, owners_user_id=owners_user_id)
            db.session.add(new_textbook)
            db.session.flush()  

            textbook_id = new_textbook.textbook_id

            filename = f"Textbook_id-{textbook_id}.jpg"       #we can change the file extension to whatever and everything will still work, just using jpg for smaller file sizes.
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            image_url = f"/static/images/{filename}"

            new_textbook.image_url = image_url
            db.session.commit()

            flash('Textbook added successfully!', category='success')
            return redirect(url_for('addDeleteTextbook'))

        else:
            flash('Please select an image for the book.', category='error')
            return redirect(url_for('addDeleteTextbook'))

    return render_template('addDeleteTextbook.html')

"""
        LEGACY METHOD
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            #----------------------Gets the id of the newly added textbook and appends it to the end of the image filename---------------
            # if textbook id = 12 and filename = image.png then this will output image12.png--------------

            new_textbook = Textbook(title=title, description=description, image_url="", price=price, owners_user_id=owners_user_id) 
            db.session.add(new_textbook)
            db.session.flush()
            textbook_id = new_textbook.textbook_id
            file_extension = filename.rsplit('.',1)[1]
            filename = f"Textbook_id-{textbook_id}.{file_extension}"

            #saves image file in static/images and updates the image url and commits new_textbook to database
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"/static/images/{filename}"
            new_textbook.image_url = image_url
            db.session.commit()


        else:

            flash('Invalid file type. Only PNG, JPG, and JPEG images are allowed.', category='error')
            return redirect(url_for('addDeleteTextbook'))

        flash('Textbook added successfully!', category='success')
        return redirect(url_for('addDeleteTextbook'))

    return render_template('addDeleteTextbook.html')
"""
@app.get('/profile')
def profile():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect(url_for('login'))
    
    user = db.session.query(users).filter(users.user_id == session['user']['user_id']).first()

    filtered_textbooks = db.session.query(Textbook).filter(Textbook.owners_user_id == user.user_id).all()

    carts = db.session.query(Cart).filter(Cart.user_id == user.user_id).first()

    if carts:
        cart_textbooks = db.session.query(Textbook).join(CartItem, CartItem.textbook_id == Textbook.textbook_id).filter(CartItem.cart_id == carts.cart_id).all()
    else:
        cart_textbooks = []

    return render_template('profile.html', user=user, filtered_textbooks=filtered_textbooks, cart_textbooks=cart_textbooks)


#app before_request runs before every single request, this just injects the profile picture url into g.profile_pic_url that is then accessed in layout.html
@app.before_request
def before_request():
    if 'user' in session:
        current_user = db.session.query(users).filter(                
                or_(
                    users.user_id == session['user']['user_id']
                )
            ).first()
        if current_user:
            g.profile_pic_url = current_user.profile_picture
        else:
            g.profile_pic_url = "/static/images/defaultPFP.png"
    else:
        g.profile_pic_url = "/static/images/defaultPFP.png"



@app.route('/add_pfp', methods=['GET', 'POST'])
def add_pfp():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    
    if request.method == 'POST':
        file = request.files.get('image')


        if file and file.filename and allowed_file(file.filename):

            #-----------sets filename to pfp_id-12.png assuming a png is uploaded and the current user's id is 12--------------
            filename = secure_filename(file.filename)
            user_id = session['user']['user_id']
            file_extension = filename.rsplit('.',1)[1]
            filename = f"pfp_id-{user_id}.{file_extension}"

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"/static/images/{filename}"

            #-----------Finds current user in databse and sets its profile_piture url to the image_url just created-------------
            user = db.session.query(users).filter(                
                or_(
                    users.user_id == session['user']['user_id']
                )
            ).first()

            if not user:
                abort(403)

            user.profile_picture = image_url
            db.session.commit()

        else:

            flash('Invalid file type. Only PNG, JPG, and JPEG images are allowed.', category='error')
            return redirect(url_for('profile'))

        flash('Pfp added successfully!', category='success')
        return redirect(url_for('profile'))

    return render_template('profile.html')


#comment for git video (Delete Later!!!)

@app.route('/del_pfp', methods=['GET', 'POST'])
def del_pfp():
    if 'user' not in session:
        flash(not_logged_in_message, category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    if request.method == 'POST':

        user = db.session.query(users).filter(
            users.user_id == session['user']['user_id']
        ).first()

        current_image_path = user.profile_picture

        default_image = "/static/images/defaultPFP.png"
        user.profile_picture = default_image
        db.session.commit()

        if current_image_path != default_image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image_path.split('/')[-1])
            if os.path.exists(image_path):
                os.remove(image_path)
            flash('Pfp deleted successfully!', category='success')
        else:
            flash("Cannot delete default profile picture", category='error')

        return redirect(url_for('profile'))

    return render_template('profile.html')

@app.get('/search')
def search():
    query = request.args.get('search_query', '').lower()
    

    #Searchs textbooks in the texbooks table and filtered_textbooks stores textbooks that match the query.
    if query:
        filtered_textbooks = db.session.query(Textbook).filter(
            or_(
                Textbook.title.ilike(f'%{query}%'),
                Textbook.description.ilike(f'%{query}%')
            )
        ).all()
    else:
        filtered_textbooks = Textbook.query.order_by(Textbook.created_at.desc()).all()

    return render_template('search_results.html', query=query, textbooks=filtered_textbooks)

@app.get('/book')
def book():
    textbook_id = request.args.get('textbook_id')
    textbook = db.session.query(Textbook).filter(Textbook.textbook_id == textbook_id).first()
    if textbook is None:
        return "Textbook not found", 404
    avg_rating = 0
    if len(textbook.ratings) > 0:
        for rating_info in textbook.ratings:
            avg_rating += rating_info.rating
        avg_rating = avg_rating / len(textbook.ratings)
        avg_rating = round(avg_rating, 1)
    order_items = OrderItem.query.filter_by(textbook_id = textbook_id).all()
    active_listings = len(textbook.owner.textbooks)


    return render_template('book.html', textbook = textbook, avg_rating = avg_rating, num_of_books_sold_by_owner = len(order_items), active_listings = active_listings)

@app.get('/about')
def about():
    return render_template('about.html')

@app.get('/login')
def login():
    if 'user' in session:
        flash("You are already logged in", category='error')
        return redirect('/')
    return render_template('login.html')

@app.post('/login')
def login_user():
    if 'user' in session:
        flash('You are already logged in', category='error')
        return redirect('/')
    user_username = request.form.get('username')
    user_password = request.form.get('password')

    if not user_username or not user_password:
        flash('Please enter a username and password', category='error')
        return redirect('/login')
    
    current_user = users.query.filter(
    (func.lower(users.username) == user_username.lower()) | 
    (func.lower(users.email) == user_password.lower())
    ).first()

    if current_user is not None:
        if bcrypt.check_password_hash(current_user.password, user_password):
                flash('Successfully logged in, ' + current_user.first_name + '!', category='success')
                user_repository_singleton.login_user(current_user)
                return redirect('/')
        else:
            flash('Incorrect username or password', category='error')
    else:
        flash('Username does not exist', category='error')

    return redirect('/login')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'user' in session:
        user_repository_singleton.logout_user()
    else:
        flash(not_logged_in_message, category='error')
    return redirect('/')

@app.get('/register')
def register():
    if 'user' in session:
        flash('You are already logged in. Logout to make a new account', category='error')
        return redirect('/')
    return render_template('register.html')

@app.post('/register')
def register_user():
    if 'user' in session:
        flash('You are already logged in. Logout to make a new account', category='error')
        return redirect('/')
    
    user_first_name = request.form.get('first-name')
    user_last_name = request.form.get('last-name')
    user_email = request.form.get('email')
    user_phone_number = request.form.get('phone-number')
    user_username = request.form.get('username')
    user_password = request.form.get('password')
    profile_picture = '/static/images/defaultPFP.png'

    if not user_username or not user_password or not user_first_name or not user_last_name or not user_email:
        flash('Please fill out all of the fields', category='error')
        return redirect('/register')

    # Check if email contains UNCC domain - removing for now for easing testing and grading
    # if not (user_email.lower().endswith('charlotte.edu') or user_email.lower().endswith('uncc.edu')):
    #     flash('Must be a UNCC student/faculty to register. Please use your UNCC email.', category='error')
    #     return redirect('/register')

    current_user = users.query.filter((func.lower(users.username) == user_username.lower()) | 
    (func.lower(users.email) == user_email.lower())).first()

    if current_user:
        if current_user.email.lower() == user_email.lower():
            flash('email already exists', category='error')
        elif current_user.username.lower() == user_username.lower():
            flash('username already exists', category='error')
        return redirect('/register')

    current_unverified_user = UnverifiedUsers.query.filter((func.lower(UnverifiedUsers.username) == user_username.lower()) | 
    (func.lower(UnverifiedUsers.email) == user_email.lower())).first()

    if current_unverified_user:
        if current_unverified_user.email.lower() == user_email.lower():
            flash('email already exists', category='error')
        elif current_unverified_user.username.lower() == user_username.lower():
            flash('username already exists', category='error')
        return redirect('/register')
    
    
    if user_repository_singleton.validate_input(user_first_name, user_last_name, user_username, user_phone_number, user_password):
        # new_user = users(user_first_name, user_last_name, user_email, user_phone_number,user_username, bcrypt.generate_password_hash(user_password).decode(), profile_picture)
        # db.session.add(new_user)
        # db.session.commit()
        # user_repository_singleton.login_user(new_user)
        new_unverified_user = UnverifiedUsers(user_first_name, user_last_name, user_email, user_phone_number,user_username, bcrypt.generate_password_hash(user_password).decode(), profile_picture)
        db.session.add(new_unverified_user)
        db.session.commit()
        code_id = generate_and_send_code(new_unverified_user.unverified_user_id, user_email)
        if code_id:
            return redirect(f'/verify_user/{code_id}')
        else:
            db.session.delete(new_unverified_user)
            db.session.commit()
            flash('Something went wrong. Please try again', category='error')
            return redirect('/register')
        # flash('Account created successfully', category='success')
    else:
        return redirect('/register')

    # return redirect('/')

@app.get('/verify_user/<uuid:code_id>')
def verify_code(code_id):
    return render_template('verify_code.html', code_id = code_id)

@app.post('/verify_user/<uuid:code_id>')
def verify_code_submission(code_id):
    user_code = request.form.get('user-code')
    
    # Check if the verification code matches and belongs to the current user
    original_code = VerificationCodes.query.filter(
        VerificationCodes.code_id == code_id,
        VerificationCodes.verification_code == user_code
    ).first()
    
    if original_code:
        if datetime.now() < original_code.expiration_timestamp:
            # Retrieve unverified user and create a verified user entry
            unverified_user = UnverifiedUsers.query.filter_by(unverified_user_id=original_code.user_id).first()
            
            if unverified_user:
                # Transfer unverified user data to a new user entry
                new_user = users(
                    first_name=unverified_user.first_name,
                    last_name=unverified_user.last_name,
                    email=unverified_user.email,
                    phone_number=unverified_user.phone_number,
                    username=unverified_user.username,
                    password=unverified_user.password,
                    profile_picture=unverified_user.profile_picture
                )
                
                # Add and commit the new verified user, then delete unverified entry
                db.session.add(new_user)
                db.session.delete(unverified_user)
                db.session.commit()
                
                # Log in the new user and redirect to the home page
                user_repository_singleton.login_user(new_user)
                flash('Account created successfully', category='success')
                return redirect('/')
            else:
                flash('Something went wrong. User not found.', category='error')
                return redirect(f'/verify_user/{code_id}')
        else:
            flash('Code has expired.', category='error')
            return redirect('/register')
    else:
        flash('Invalid code', category='error')
        return redirect(f'/verify_user/{code_id}')

@app.get('/cart/<uuid:cart_id>')
def get_cart(cart_id):
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect('/login')
    cart_items_dict = {}
    rentals = {}
    total = 0.00

    cart = Cart.query.filter_by(cart_id=cart_id).first()
    if not cart:
        flash('Something went wrong', category='error')
        return redirect(request.referrer)
    
    cart_items = CartItem.query.filter_by(cart_id = cart_id).all()
    for item in cart_items:
        textbook = Textbook.query.filter(Textbook.textbook_id == item.textbook_id).first()

        if textbook and item.checkout_type == 'buy':
            total += float(textbook.price * item.quantity)
            cart_items_dict[textbook.textbook_id] = {
                'title' : textbook.title,
                'description' : textbook.description,
                'price' : textbook.price,
                'quantity' : item.quantity,
                'image_url': textbook.image_url,
                'total' : (item.quantity * textbook.price)
            }
        elif textbook and item.checkout_type == 'rent':
            rental_price = textbook.price * Decimal('0.45') if item.duration == 8 else textbook.price * Decimal('0.70') 
            due_date = datetime.now() + timedelta(weeks=8) if item.duration == 8 else datetime.now() + timedelta(weeks=16)
            total += float(rental_price)
            rentals[textbook.textbook_id] = {
                'title' : textbook.title,
                'description' : textbook.description,
                'price' : rental_price,
                'duration' : item.duration,
                'image_url': textbook.image_url,
                'due_date': due_date
            }
    final_price = round(total, 2)

    return render_template('cart.html', cart = cart_items_dict, total = total, final_price = final_price, rentals = rentals)

@app.post('/cart/<uuid:cart_id>')
def add_cart_item(cart_id):
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect('/login')
    textbook_id = request.form.get('textbook_id')
    if not textbook_id:
        flash('Something went wrong. Please try again')
        return redirect(request.referrer)

    cart = Cart.query.filter_by(cart_id=cart_id).first()
    if not cart:
        flash('Something went wrong', category='error')
        return redirect(request.referrer)

    textbook = CartItem.query.filter(
    and_(CartItem.cart_id == cart_id, CartItem.textbook_id == textbook_id)).first()

    if textbook and textbook.checkout_type == 'rent':
        flash('Item is already in cart for either rent or purchase.', category='error')
        return redirect(request.referrer)
    if textbook:
        textbook.quantity += 1
    else:
        new_item = CartItem(cart_id, textbook_id, 1)
        db.session.add(new_item)

    db.session.commit()
    user_repository_singleton.update_cart_quantity()

    return redirect(f'/cart/{cart_id}')

@app.post('/cart/delete/<uuid:cart_id>')
def delete_cart_item(cart_id):
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect('/login')
    textbook_id = request.form.get('textbook_id')
    if not textbook_id:
        abort(404)
    textbook = CartItem.query.filter(
    and_(CartItem.cart_id == cart_id, CartItem.textbook_id == textbook_id)).first()

    if textbook:
        db.session.delete(textbook)
        db.session.commit()

    user_repository_singleton.update_cart_quantity()

    return redirect(f'/cart/{cart_id}')

@app.post('/cart/update/<uuid:cart_id>')
def update_item_quantity(cart_id):
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect('/login')
    textbook_id = request.form.get('textbook_id')
    updated_quantity = request.form.get('textbook_quantity')
    if not textbook_id:
        abort(404)
    textbook = CartItem.query.filter(
    and_(CartItem.cart_id == cart_id, CartItem.textbook_id == textbook_id)).first()

    if textbook:
        textbook.quantity = updated_quantity

    db.session.commit()
    
    user_repository_singleton.update_cart_quantity()
    
    return redirect(f'/cart/{cart_id}')

@app.post('/book/<uuid:textbook_id>/rent')
def add_rental_to_cart(textbook_id):
    if 'user' not in session:
        flash(not_logged_in_message, category='error')
        return redirect('/login')
    if not textbook_id:
        flash('Something went wrong. Please try again', category='error')
        return redirect(request.referrer)
    
    print(session['cart']['cart_id'])
    cart_id = request.form.get('cart_id')
    duration = request.form.get('duration')
    duration = 8 if duration == '1' else 16

    textbook = CartItem.query.filter(
    and_(CartItem.cart_id == cart_id, CartItem.textbook_id == textbook_id)).first()

    if textbook:
        flash('Item is already in cart for either rent or purchase.', category='error')
        return redirect(request.referrer)
    else:
        new_item = CartItem(cart_id, textbook_id, 1, 'rent', duration)
        db.session.add(new_item)

    db.session.commit()
    user_repository_singleton.update_cart_quantity()

    return redirect(f'/cart/{cart_id}')
    

@app.route('/create_meetup', methods=['POST', 'GET'])
def create_meetup():
    if 'user' in session:
        if request.method == 'POST':
            host_id = session['user']['user_id']
            meeting_description = request.form['meeting_description']
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            user_address = request.form['user_address']
            textbook_id = request.form['textbook_id']
            
            geocode_result = gmaps.geocode(user_address)
            meeting_address_pre = geocode_result[0]["place_id"]
            rev_geocode_result = gmaps.reverse_geocode(meeting_address_pre)
            user_address = rev_geocode_result[0]["formatted_address"]
            
            if not host_id or not meeting_description or not start_time or not end_time:
                flash('Please fill out all the fields', category='error')
                return redirect('/create_meetup')
            
            #check if a meetup already exists for the textbook
            existing_meetup = Meetup.query.filter_by(textbook_id=textbook_id).first()
            if existing_meetup:
                #update the existing meetup
                existing_meetup.user_id = host_id
                existing_meetup.meeting_description = meeting_description
                existing_meetup.start_time = start_time
                existing_meetup.end_time = end_time
                existing_meetup.user_address = user_address
                db.session.commit()
                return redirect(f'/view_meetup/{existing_meetup.textbook_id}')
            else:
                #create a new meeting entry
                new_meeting = Meetup(
                    user_id=host_id,
                    textbook_id=textbook_id,
                    meeting_description=meeting_description,
                    start_time=start_time,
                    end_time=end_time,
                    user_address=user_address
                )
                db.session.add(new_meeting)
                db.session.commit()
                return redirect(f'/view_meetup/{new_meeting.textbook_id}')
        else:
            textbook_id = request.args.get('textbook_id')
            return render_template('create_meetup.html', textbook_id=textbook_id)
    else:
        return redirect('/login')
    
@app.route('/view_meetup/<textbook_id>')
def view_meetup(textbook_id):
    meetup = Meetup.query.filter_by(textbook_id=textbook_id).first()
    if meetup:
        return render_template('view_meetup.html', meetup=meetup)
    else:
        flash('Meetup location has not been set for this book yet', category='error')
        return redirect(request.referrer)

# To test checkout, reference STRIPE API TEST documentation or enter 
# '4242 4242 4242 4242' as credit card 
# Use a valid future date, such as 12/34
# Use any three-digit CVC (four digits for American Express cards)
# Use any value you like for other form fields
@app.post('/create-checkout-session')
def checkout():
    cart_items = CartItem.query.filter_by(cart_id = session['cart']['cart_id']).all()
    if cart_items is None:
        abort(404)
    line_items = []
    for item in cart_items:
        textbook = Textbook.query.filter(Textbook.textbook_id == item.textbook_id).first()
        if textbook:
            if item.checkout_type == 'rent': 
                curr_price = textbook.price * Decimal('.45') if item.duration == 8 else textbook.price * Decimal('.70')
            line_items.append({
                'price_data': {
                    'currency' : 'usd',
                    'product_data' : {
                        'name' : textbook.title,
                        'description' : textbook.description
                    },
                    'unit_amount' : int((curr_price * 100)),
                },
                'quantity': item.quantity,
            })

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items = line_items,
            mode = "payment",
            success_url = url_for('home', _external=True, success="true"),
            cancel_url = url_for('get_cart', cart_id = session['cart']['cart_id'], _external=True)
        )
        if not checkout_session.url:
            abort(404)
        return redirect(checkout_session.url)
    except Exception as e:
        flash('Error. Transaction failed', category="error")
        return redirect('/')

# This is the get endpoint when user visits the DM's page
@app.get('/direct_messaging')
def get_dms_page():
    if 'user' not in session:
        flash(not_logged_in_message, category="error")
        return redirect('/login')
    
    user_id = session['user']['user_id']
    # seller ID if passed as a query parameter, would be a parameter if user buys a book for pickup then they
    # would be redirected to DM's page with seller selected to chat with
    seller_id = request.args.get('seller_id')
    textbook_id = request.args.get('textbook_id')
    
    # get all users conversations. Filters can be confusing but we want all convos where user has sent a msg or 
    # rceieved one hence user id for both filter 
    conversations = Conversations.query.filter(
        (Conversations.sender_user_id == user_id) |
        (Conversations.receiver_user_id == user_id)
    ).all()

    selected_conversation = None
    # If a user came from purchasing a book, check if they have an exsisting conversation
    # We want to create a convo if doesnt exist between seller and buyer and the textbook_id
    if seller_id and str(seller_id) != str(user_id):  
        selected_conversation = Conversations.query.join(Textbook, Conversations.textbook_id == Textbook.textbook_id).filter(
            (
                (Conversations.sender_user_id == user_id) & (Conversations.receiver_user_id == seller_id)
            ) |
            (
                (Conversations.receiver_user_id == user_id) & (Conversations.sender_user_id == seller_id)
            )
        ).filter(
            Textbook.textbook_id == textbook_id
        ).first()

        # If it doesn't exist, create it as new convo and append one
        if not selected_conversation and textbook_id:
            selected_conversation = Conversations(sender_user_id = user_id, receiver_user_id = seller_id, textbook_id=textbook_id)
            db.session.add(selected_conversation)
            db.session.commit()
            conversations.append(selected_conversation)

    return render_template('direct_messaging.html', conversations=conversations, selected_conversation=selected_conversation)

@app.post('/direct_messaging')
def append_message():
    message = request.form.get('text')
    receiver_id = request.form.get('receiver_id')
    textbook_id = request.form.get('textbook_id')
    current_conversation = Conversations.query.filter(
        ((Conversations.sender_user_id == session['user']['user_id']) & (Conversations.receiver_user_id == receiver_id)) |
        ((Conversations.receiver_user_id == session['user']['user_id']) & (Conversations.sender_user_id == receiver_id))
    ).first()

    current_conversation = Conversations.query.join(Textbook, Conversations.textbook_id == Textbook.textbook_id).filter(
            (
                (Conversations.sender_user_id == session['user']['user_id']) & (Conversations.receiver_user_id == receiver_id)
            ) |
            (
                (Conversations.receiver_user_id == session['user']['user_id']) & (Conversations.sender_user_id == receiver_id)
            )
        ).filter(
            Textbook.textbook_id == textbook_id
        ).first()

    if message and current_conversation:
        msg = Messages(session['user']['user_id'], current_conversation.conversation_id, message)
        db.session.add(msg)
        db.session.commit()

        user = users.query.filter(users.user_id == msg.user_id).first()
        message_data = {
            "user_id": msg.user_id,
            "text": msg.message_text,
            "created_at": msg.created_at,
            "img": user.profile_picture if user else ""
        }
        return jsonify({'status': 'success', 'message': message_data})

    return jsonify({'status': 'error', 'message': 'Message not sent'})

# This is the get endpoint used for the ajax calls just to get the messages so page isnt reloaded
@app.get('/load_messages/<user_id>/<textbook_id>')
def load_messages(user_id, textbook_id):
    current_user_id = session['user']['user_id']
    # conversation = Conversations.query.filter(
    #     (Conversations.sender_user_id == current_user_id) & 
    #     (Conversations.receiver_user_id == user_id) |
    #     (Conversations.receiver_user_id == current_user_id) & 
    #     (Conversations.sender_user_id == user_id) 
    # ).first()

    conversation = Conversations.query.join(Textbook, Conversations.textbook_id == Textbook.textbook_id).filter(
            (
                (Conversations.sender_user_id == current_user_id) & (Conversations.receiver_user_id == user_id)
            ) |
            (
                (Conversations.receiver_user_id == current_user_id) & (Conversations.sender_user_id == user_id)
            )
        ).filter(
            Textbook.textbook_id == textbook_id
        ).first()

    if conversation:
        messages = Messages.query.filter_by(conversation_id = conversation.conversation_id).all()
        messages_data = []
        for msg in messages:
            user = users.query.filter(users.user_id == msg.user_id).first()
            messages_data.append({
                "user_id": msg.user_id, 
                "text": msg.message_text, 
                "created_at": msg.created_at,
                "img": user.profile_picture if user else ""
            })
        return jsonify({"messages": messages_data})
    return jsonify({"messages": []}) 

@app.post('/conversation/<uuid:conversation_id>/delete')
def delete_conversation(conversation_id):
    # Delete all messages of conversation and conversation
    messages = Messages.query.filter_by(conversation_id = conversation_id).delete()
    conversation = Conversations.query.filter_by(conversation_id = conversation_id).delete()
    if not conversation:
        flash('Something went wrong', category='error')
        return redirect('/direct_messaging')
    db.session.commit()
    flash('Conversation has been deleted', category='success')
    return redirect('/direct_messaging')

@app.post('/conversation/<uuid:conversation_id>/confirm')
def confirm_order(conversation_id):
    if 'user' not in session:
        abort(403)
    
    conversation = Conversations.query.filter_by(conversation_id=conversation_id).first()
    if not conversation:
        flash('Something went wrong', category='error')
        return redirect('/direct_messaging')
    
    # Only the buyer (sender) can confirm the pickup
    if conversation.sender_user_id != session['user']['user_id']:
        flash('Only the buyer can confirm pickup', category='error')
        return redirect('/direct_messaging')
    
    # Add order
    new_order = Order(session['user']['user_id'], conversation.textbook.price, 'Complete')
    order_item = OrderItem(new_order.order_id, conversation.textbook.textbook_id, 1)
    db.session.add(new_order)
    db.session.add(order_item)
    
    # Delete all messages related to the conversation and conversation
    Messages.query.filter_by(conversation_id=conversation_id).delete()
    db.session.delete(conversation) 
    
    db.session.commit()
    
    flash('Pickup has been confirmed. Please visit the orders page to rate your order', category='success')
    return redirect('/direct_messaging')


@app.get('/request_password_reset')
def get_password_request_page():
    if 'user' in session:
        flash('You are already logged in', category='error')
        return redirect('/')
    return render_template('request_password_reset.html')

@app.post('/request_password_reset')
def send_password_request():
    user_email = request.form.get('email')

    if not user_email:
        flash('Please enter an email address.', category='error')
        return redirect('/request_password_reset')
    
    actual_email_user = users.query.filter_by(email = user_email).first()
    if not actual_email_user:
        flash('Account with entered email does not exist.', category='error')
        return redirect('/request_password_reset')

    # password_reset_code = uuid4()
    token = actual_email_user.get_reset_token()
    if not token:
        abort(403)
    reset_url = url_for('get_reset_password_page', token=token, _external=True)
    message = Mail(
    from_email='bookborrow763@gmail.com',
    to_emails=actual_email_user.email,
    subject='BookBorrow Reset Password Link',
    html_content=f"""
        <p>Click the link below to reset your password:</p>
        <a href="{reset_url}">Password Reset Link</a>
        <p>If you did not make this request, please ignore this email.</p>
    """
    )   
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        flash('Email Successfully sent. Follow the instructions to reset your email', category='success')
        return redirect('/login')
    except Exception as e:
        print(e)
        flash('Something went wrong. Please try again later', category='error')
        return redirect('/request_password_reset')
    
@app.get('/reset_password/<token>')
def get_reset_password_page(token):
    if 'user' in session:
        flash('You are already logged in', category='error')
        return redirect('/')
    user = users.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', category='error')
        return redirect('/login')
    return render_template('reset_password.html', token=token)

@app.post('/reset_password/<token>')
def reset_password(token):
    if 'user' in session:
        flash('You are already logged in', category='error')
        return redirect('/')
    user = users.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', category='error')
        return redirect('/login')
    
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')

    if not password or not confirm_password:
        flash('Please fill out all fields', category='error')
        return redirect('/reset_password')
    if password != confirm_password:
        flash('Passwords do not match', category='error')
        return redirect('/reset_password')
    if (len(password) < 6) or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or any(char.isspace() for char in password):
        flash('Password must contain at least 6 characters, a letter, a number, and no spaces', category='error')
        return redirect(f'/password_reset/{token}')

    user.password = bcrypt.generate_password_hash(password).decode()
    db.session.commit()
    flash('Password reset successfully!', category='success')
    return redirect('/login')

@app.get('/orders')
def get_orders():
    if 'user' not in session:
        flash(not_logged_in_message, 'error')
        return redirect('/login')
    orders = {}
    user_orders = Order.query.filter_by(user_id = session['user']['user_id']).all()
    for order in user_orders:
        order_items = OrderItem.query.filter_by(order_id = order.order_id).all()
        orders[str(order.order_id)] = {
            'status': order.status,
            'orderItems': order_items,
            'total_price' : order.price,
            'order_date' : order.order_date.strftime("%m/%d/%Y")
        }
    return render_template('orders.html', orders = orders)

@app.post('/orders/<uuid:order_id>/confirm')
def move_order_to_confirmed(order_id):
    order = Order.query.filter_by(order_id = order_id).first()
    if order:
        order.status = "Completed"
        db.session.commit()
        flash('Order moved to completed', category='success')
        return redirect('/orders')
    flash('Could not mark order as completed', category='error')
    return redirect('/orders')

@app.get('/orders/<uuid:textbook_id>/rate-textbook')
def get_rate_textbook_page(textbook_id):
    if 'user' not in session:
        flash(not_logged_in_message, 'error')
        return redirect('/')
    rating = Rating.query.filter(and_(Rating.user_id == session['user']['user_id'], Rating.textbook_id == textbook_id)).first()
    if rating:
        flash("You have already rated this book", category='error')
        return redirect('/orders')
    textbook = Textbook.query.filter_by(textbook_id = textbook_id).first()
    if not textbook:
        flash("something went wrong", category='error')
        return redirect('/orders')
    return render_template('rate_textbook.html', textbook = textbook)

@app.post('/orders/<uuid:textbook_id>/rate-textbook')
def submit_rate_textbook_page(textbook_id):
    if 'user' not in session:
        flash(not_logged_in_message, 'error')
        return redirect('/')
    textbook = Textbook.query.filter_by(textbook_id = textbook_id).first()
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    if textbook and rating and comment:
        rating = Rating(session['user']['user_id'], textbook_id, rating, comment)
        db.session.add(rating)
        db.session.commit()
        flash('Thank you for leaving a rating!', category='sucess')
        return redirect('/')
    elif textbook and rating:
        rating = Rating(session['user']['user_id'], textbook_id, rating, )
        db.session.add(rating)
        db.session.commit()
        flash('Thank you for leaving a rating!', category='sucess')
        return redirect('/')
    flash('Something went wrong. Unable to leave rating', category='error')
    return redirect('/orders')
    
@app.route('/mostSold')
def most_sold():
    all_orders = OrderItem.query.all() 
    max_quantity_sold = 0
    textbooks = {}
    
    for order_item in all_orders:
        textbook = Textbook.query.filter_by(textbook_id=order_item.textbook_id).first()
        if not textbook:
            flash('Something went wrong', category='error')
            return redirect(request.referrer)
        
        if textbook.textbook_id in textbooks:
            textbooks[textbook.textbook_id] += order_item.quantity
        else:
            textbooks[textbook.textbook_id] = order_item.quantity
    
    most_sold_book = None
    max_quantity_sold = 0
    for textbook_id, quantity in textbooks.items():
        if quantity > max_quantity_sold:
            most_sold_book = Textbook.query.filter_by(textbook_id=textbook_id).first()
            max_quantity_sold = quantity
    
    # Render the result
    return render_template('mostSold.html', book=most_sold_book)

if __name__ == '__main__':
    app.run(debug=True)
