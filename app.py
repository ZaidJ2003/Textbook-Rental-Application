# To run, must create virtual env and activate it, then run flask run

from flask import Flask, abort, redirect, render_template, request, url_for, flash, jsonify, session, blueprints
import os
from dotenv import load_dotenv
from src.models import db, users, Textbook, Cart, CartItem, Messages, Conversations
from sqlalchemy import or_, func, and_
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from src.repositories.user_repository import user_repository_singleton
import googlemaps
import stripe
from flask import g
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

#global test api key for Stripe
stripe.api_key = 'sk_test_51Q6zr6BsbRXEeqR8BeQBHg39OmzSwbOOw3YHFCKV42pl0InBUCq2zOIwjMXgyzCxDEYvuziLlLl8ayjZKnBPPlPm00EtEGae67'

@app.get('/')
def home():
    if request.args.get('success') == "true":
        user_repository_singleton.clear_cart()
        flash("Transaction successful!", category="success")
    return render_template('index.html')

@app.get('/addDeleteTextbook')
def addDeleteTextbook():
    if 'user' not in session:
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
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
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
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
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')        #gets info from the form and the current users id
        price = request.form.get('price')
        owners_user_id = session['user']['user_id']
        file = request.files.get('image')


        if file and allowed_file(file.filename):
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

@app.get('/profile')
def profile():
    if 'user' not in session:
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    user = db.session.query(users).filter(                
        or_(
            users.user_id == session['user']['user_id']
        )
    ).first()

    image_url = user.profile_picture

    return render_template('profile.html', image_url=image_url)

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
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
        return redirect(url_for('login'))
    
    
    if request.method == 'POST':
        file = request.files.get('image')


        if file and allowed_file(file.filename):

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
        flash("You need to log in to access this page.", category='error')        #makes sure the user is logged in, if they aren't they get redirected to the login page
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

    return render_template('book.html', textbook = textbook)

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

@app.post('/logout')
def logout():
    if 'user' in session:
        user_repository_singleton.logout_user()
    else:
        flash('You are not logged in', category='error')
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
    user_username = request.form.get('username')
    user_password = request.form.get('password')
    profile_picture = '/static/images/defaultPFP.png'

    if not user_username or not user_password or not user_first_name or not user_last_name or not user_email:
        flash('Please fill out all of the fields', category='error')
        return redirect('/register')

    current_user = users.query.filter((func.lower(users.username) == user_username.lower()) | 
    (func.lower(users.email) == user_email.lower())).first()

    if current_user:
        if current_user.email.lower() == user_email.lower():
            flash('email already exists', category='error')
        elif current_user.username.lower() == user_username.lower():
            flash('username already exists', category='error')
        return redirect('/register')
    
    if user_repository_singleton.validate_input(user_first_name, user_last_name, user_username, user_password):
        new_user = users(user_first_name, user_last_name, user_email, user_username, bcrypt.generate_password_hash(user_password).decode(), profile_picture)
        db.session.add(new_user)
        db.session.commit()
        user_repository_singleton.login_user(new_user)
        flash('Account created successfully', category='success')
    else:
        return redirect('/register')

    return redirect('/')

@app.get('/cart/<uuid:cart_id>')
def get_cart(cart_id):
    if 'user' not in session:
        flash('Must be logged in to access cart and checkout')
        return redirect('/login')
    cart_items_dict = {}
    total = 0.00
    if 'cart' in session:
        # for id, value in session['cart'].items():
        #     textbook = Textbook.query.filter(Textbook.textbook_id == id).first()
        #     if textbook:
        #         cart_books[textbook] = value
        cart_items = CartItem.query.filter(CartItem.cart_id == cart_id).all()
        for item in cart_items:
            textbook = Textbook.query.filter(Textbook.textbook_id == item.textbook_id).first()
            if textbook:
                total += float(textbook.price * item.quantity)
                cart_items_dict[textbook.textbook_id] = {
                    'title' : textbook.title,
                    'description' : textbook.description,
                    'price' : textbook.price,
                    'quantity' : item.quantity,
                    'image_url': textbook.image_url,
                    'total' : (item.quantity * textbook.price)
                }
    # tax = round(total * .0475,2)
    final_price = round(total, 2)
    return render_template('cart.html', cart = cart_items_dict, total = total, final_price = final_price)

@app.post('/cart/<uuid:cart_id>')
def add_cart_item(cart_id):
    if 'user' not in session:
        flash('Must be logged in to access cart and checkout')
        return redirect('/login')
    textbook_id = request.form.get('textbook_id')
    if not textbook_id:
        abort(404)
    textbook = CartItem.query.filter(
    and_(CartItem.cart_id == cart_id, CartItem.textbook_id == textbook_id)).first()

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
        flash('Must be logged in to access cart and checkout')
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

#temporary meetup page (specifically made to implement gmaps)
@app.post('/meetup')
def meetup():
    if 'user_id' in session:
        host_id = session['user_id']
        meeting_name = request.form['meeting_name']
        meeting_description = request.form['meeting_description']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        user_address = request.form['user_address']
        
        geocode_result = gmaps.geocode(user_address)
        meeting_address_pre = geocode_result[0]["place_id"]

        rev_geocode_result = gmaps.reverse_geocode(meeting_address_pre)
        meeting_address = rev_geocode_result[0]["formatted_address"]
        
        if not host_id or not meeting_name or not meeting_description or not start_time or not end_time:
            return 'Bad Request', 400
        # More tests???????
        return redirect('/meetup')
    else:
        return render_template('index.html')
    
#temporary meetup page (specifically made to implement gmaps)
@app.get('/meetup')
def meetup_page():
        return render_template('meetup.html')

@app.post('/cart/update/<uuid:cart_id>')
def update_item_quantity(cart_id):
    if 'user' not in session:
        flash('Must be logged in to access cart and checkout')
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

# To test checkout, reference STRIPE API TEST documentation or enter 
# '4242 4242 4242 4242' as credit card 
# Use a valid future date, such as 12/34
# Use any three-digit CVC (four digits for American Express cards)
# Use any value you like for other form fields
@app.post('/create-checkout-session')
def checkout():
    cart_items = CartItem.query.filter(CartItem.cart_id == session['cart']['cart_id']).all()
    if cart_items is None:
        abort(404)
    line_items = []
    for item in cart_items:
        textbook = Textbook.query.filter(Textbook.textbook_id == item.textbook_id).first()
        if textbook:
            line_items.append({
                'price_data': {
                    'currency' : 'usd',
                    'product_data' : {
                        'name' : textbook.title,
                        'description' : textbook.description
                    },
                    'unit_amount' : int((textbook.price * 100)),
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

# TO-DO: Fix having to refresh before new convo loads
# Fix positioning of msg bar to be fixed

# This is the get endpoint when user visits the DM's page
@app.get('/direct_messaging')
def get_dms_page():
    if 'user' not in session:
        flash("Must be logged in to access DM's page", category="error")
        return redirect('/login')
    
    user_id = session['user']['user_id']
    # seller ID if passed as a query parameter, would be a parameter if user buys a book for pickup then they
    # would be redirected to DM's page with seller selected to chat with
    seller_id = request.args.get('seller_id')
    
    # get all users conversations. Filters can be confusing but we want all convos where user has sent a msg or 
    # rceieved one hence user id for both filter 
    conversations = Conversations.query.filter(
        (Conversations.sender_user_id == user_id) |
        (Conversations.receiver_user_id == user_id)
    ).all()

    selected_conversation = None
    # If a user came from purchasing a book, check if they have an exsisting conversation
    if seller_id and str(seller_id) != str(user_id):  
        selected_conversation = Conversations.query.filter(
            ((Conversations.sender_user_id == user_id) & (Conversations.receiver_user_id == seller_id)) |
            ((Conversations.receiver_user_id == user_id) & (Conversations.sender_user_id == seller_id))
        ).first()

        # If it doesn't exist, create it as new convo and append one
        if not selected_conversation:
            selected_conversation = Conversations(sender_user_id = user_id, receiver_user_id = seller_id)
            db.session.add(selected_conversation)
            db.session.commit()
            conversations.append(selected_conversation)

    return render_template('direct_messaging.html', conversations=conversations, selected_conversation=selected_conversation)

@app.post('/direct_messaging')
def append_message():
    message = request.form.get('text')
    receiver_id = request.form.get('receiver_id')
    current_conversation = Conversations.query.filter(
        ((Conversations.sender_user_id == session['user']['user_id']) & (Conversations.receiver_user_id == receiver_id)) |
        ((Conversations.receiver_user_id == session['user']['user_id']) & (Conversations.sender_user_id == receiver_id))
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
@app.get('/load_messages/<user_id>')
def load_messages(user_id):
    current_user_id = session['user']['user_id']
    conversation = Conversations.query.filter(
        (Conversations.sender_user_id == current_user_id) & 
        (Conversations.receiver_user_id == user_id) |
        (Conversations.receiver_user_id == current_user_id) & 
        (Conversations.sender_user_id == user_id)
    ).first()

    if conversation:
        messages = Messages.query.filter(Messages.conversation_id == conversation.conversation_id).all()
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

if __name__ == '__main__':
    app.run(debug=True)
