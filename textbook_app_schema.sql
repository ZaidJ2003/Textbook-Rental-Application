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
