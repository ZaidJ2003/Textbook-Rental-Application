## Project Overview
This project will be a textbook/kit marketplace where students at UNCC can sell their old textbooks/kits to other students. This web application will allow students to search for textbooks/kits and message sellers. It allows them to pick a meetup location to make the transaction (whether that be with cash or using a service like paypal). There will also be a review system allowing buyers to review sellers on things such as the quality of their textbooks/kits. The benefits of this softwares completion would be, helping students save money on textbooks/kits, reducing waste (people buying textbooks and kits just to sit on a shelf after the class is over), and allowing students to make their money back.

Technologies Used:
-Python
-Flask
-PostgreSQL
-HTML/CSS/JavaScript

Project Name: BookBorrow

## Setup Instructions

Create a virtual environment:

python3 -m venv venv

Activate the virtual environment:

source venv/bin/activate

Install the dependencies:

pip install -r requirements.txt

Create a file called ".env" which should have the variables in the file ".env-sample". set the variables to appropriate values

Create the PostgreSQL database using the schema in the textbook_app_schema.sql file. Can use terminal or DataGrip Application which is free for students

Run with "flask run --debug"

## Usage Details:
Students can use the application to search for desried textbooks, view available listings, and rent/purchase textbook if they decide to. The app will also provide the option to communicate with the owner of the book to faciliate the meeting or sell/return of the book.

## Team's Progress:
Completed user management/session related issues, DB creation and manipulation, basic research, Ui design, and basic search textbook functionality
