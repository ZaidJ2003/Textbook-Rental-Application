CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users(
    user_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    registration_date TIMESTAMP,
    profile_picture VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS textbooks (
    textbook_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    owners_user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    image_url VARCHAR(255),
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owners_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Added user to be the owner of all AI-generated Textbooks
--Added user to be the owner of all AI generated Textbooks
INSERT INTO users (first_name, last_name, email, username, password, phone_number, registration_date, profile_picture)
VALUES
('John', 'Stones', 'Test@example.com', 'username', 'password', '0000000000' , CURRENT_TIMESTAMP, '/static/images/defaultPFP.png');

INSERT INTO textbooks (owners_user_id, title, description, image_url, price)
VALUES
((SELECT user_id FROM users WHERE first_name = 'John'), 'Introduction to Python', 'A beginner''s guide to Python programming.', '/static/images/bookborrowlogo.jpg', 29.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Advanced Python Programming', 'Deep dive into advanced Python concepts.', '/static/images/bookborrowlogo.jpg', 49.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Data Science with Python', 'Learn data science techniques using Python.', '/static/images/bookborrowlogo.jpg', 39.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'JavaScript: The Good Parts', 'A concise guide to the best features of JavaScript.', '/static/images/bookborrowlogo.jpg', 34.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'JavaScript: The Definitive Guide', 'An in-depth guide to JavaScript programming.', '/static/images/bookborrowlogo.jpg', 44.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'The Pragmatic Programmer', 'Tips and techniques for modern software development.', '/static/images/bookborrowlogo.jpg', 42.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Clean Code', 'A handbook of agile software craftsmanship.', '/static/images/bookborrowlogo.jpg', 37.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Classic design patterns for object-oriented programming.', '/static/images/bookborrowlogo.jpg', 49.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Introduction to Machine Learning', 'Basics of machine learning and practical applications.', '/static/images/bookborrowlogo.jpg', 45.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Artificial Intelligence: A Modern Approach', 'Comprehensive overview of AI principles and techniques.', '/static/images/bookborrowlogo.jpg', 59.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Algorithms Unlocked', 'A gentle introduction to algorithms and data structures.', '/static/images/bookborrowlogo.jpg', 31.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'The Art of Computer Programming', 'Foundational text on algorithms and programming techniques.', '/static/images/bookborrowlogo.jpg', 69.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Computer Systems: A Programmer''s Perspective', 'Insight into the underlying workings of computer systems.', '/static/images/bookborrowlogo.jpg', 52.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Operating System Concepts', 'Essential concepts of modern operating systems.', '/static/images/bookborrowlogo.jpg', 46.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Database System Concepts', 'Comprehensive guide to database systems and their use.', '/static/images/bookborrowlogo.jpg', 48.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Computer Networking: A Top-Down Approach', 'Introduction to networking concepts from a top-down perspective.', '/static/images/bookborrowlogo.jpg', 41.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Introduction to the Theory of Computation', 'Foundational concepts in computational theory.', '/static/images/bookborrowlogo.jpg', 39.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Elements of Programming Interviews', 'Solutions to challenging programming interview questions.', '/static/images/bookborrowlogo.jpg', 36.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Eloquent JavaScript', 'A modern introduction to JavaScript programming.', '/static/images/bookborrowlogo.jpg', 29.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Python for Data Analysis', 'Using Python for analyzing and visualizing data.', '/static/images/bookborrowlogo.jpg', 32.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Learning SQL', 'An introduction to SQL and database querying.', '/static/images/bookborrowlogo.jpg', 27.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'Web Design with HTML, CSS, JavaScript and jQuery Set', 'Comprehensive guide to web design and development.', '/static/images/bookborrowlogo.jpg', 55.99),
((SELECT user_id FROM users WHERE first_name = 'John'), 'React Up & Running', 'Hands-on guide to building modern web applications with React.', '/static/images/bookborrowlogo.jpg', 39.99);


CREATE TABLE IF NOT EXISTS carts(
    cart_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cart_items (
    item_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    cart_id UUID NOT NULL,
    textbook_id UUID NOT NULL,
    quantity INT,
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    sender_user_id UUID NOT NULL,
    receiver_user_id UUID NOT NULL,
    textbook_id UUID NOT NULL,
    meetup_location VARCHAR(255),
    FOREIGN KEY (sender_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS unverified_users (
    unverified_user_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    registration_date TIMESTAMP,
    profile_picture VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS verification_codes (
    code_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    verification_code VARCHAR(255) NOT NULL,
    expiration_timestamp TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE, 
    FOREIGN KEY (user_id) REFERENCES unverified_users(unverified_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    order_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'pending',
    price NUMERIC(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    order_id UUID NOT NULL,
    textbook_id UUID NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    textbook_id UUID NOT NULL,
    user_id UUID REFERENCES users(user_id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meetups(
    meeting_id            UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID, 
    textbook_id UUID,
    meeting_description   VARCHAR(255)    NOT NULL,
    start_time          TIMESTAMP       NOT NULL,
    end_time            TIMESTAMP       NOT NULL,
    user_address       VARCHAR(255)    NOT NULL,       
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
);

