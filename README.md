# Library-Service

### About the Project

This project is an online library management system that helps modernize outdated processes. It replaces manual accounting of paper books and rentals with a fully automated system, optimizing the work of administrators and making the service more user-friendly.

The project is implemented as a backend service, accessed via an API.

### Key Features

- Book Management: Allows you to add, update, and delete books, as well as track their availability (inventory).


- User Management: Provides registration, login, and management of user profiles.


- Rental Accounting: Allows users to borrow and return books, and tracks return deadlines.


- Notifications: Uses Telegram to send notifications to users about new rentals, overdue books, and successful payments.


Run with docker
---------------
- docker-compose build 
- docker-compose up

# Installing using GitHub

Install PostgresSQL and create db
---------------------------------

git clone https://github.com/Shulika2407/media-service.git

cd airport-service

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

set DB_HOST=<"your db hostname">

set DB_NAME=<"your db name">

set DB_USER=<"your db username">

set DB_PASSWORD=<"your db user password">

set SECRET_KEY=<"your secret key">

python manage.py migrate

python manage.py runserver