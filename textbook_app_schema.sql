CREATE DATABASE textbook_application;

CREATE TABLE IF NOT EXISTS users(
    user_id SERIAL, --Serial auto increments id
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP,
    profile_picture VARCHAR(255), 
    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS cart(
    cart_id SERIAL;
    user_id INTEGER;
    PRIMARY KEY (cart_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE cart_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    cart_id INT,
    textbook_id INT,
    quantity INT,
    FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
    FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id)
);
