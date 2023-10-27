# Library Management System

An online management system for book borrowings that optimizes the work of library administrators and makes the service more user-friendly.

## Features

**Authentication and Authorization**:

* Users need to be authenticated before they can access the features of the system.
* Admin users have additional privileges to manage information within the system.

**Books Inventory Management**:

* The system manages the inventory of books, allowing CRUD operations for books.

**Borrowing Management**:

* Users can borrow books and create borrowing records.
* Users can return books, updating the inventory accordingly.
* Filtering for active borrowings and specific users' borrowings is available.

**Users Management**:

* The system manages user authentication and user registration.
* Users can update their profile information.

**Notifications**:

* The system sends notifications about new borrowings created, overdue borrowings, and successful payments.
* Notifications are sent through a Telegram chat.

**Payments Handling**:

* The system supports payments for book borrowings through the Stripe platform.

**Swagger Documentation**

## Architecture

The database structure is as follows:

![Database Structure](demo/library_db.png)

## Installation

### Using GitHub

1. Clone the repository:

```shell
git clone https://github.com/OlegatorLE/library-team-project
cd library-team-project
```

2. Set up the virtual environment and install the required dependencies:

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Generate a .env file from .env.sample.


4. Run the database migrations and load initial data:

```shell
python manage.py migrate
python manage.py loaddata library_db_data.json
```

5. Run the development server:
```shell
python manage.py runserver
```
## Run with Docker
* Ensure Docker is installed and set up.

* Execute the following command to build and start the Docker containers:

```shell
docker-compose up --build
```

## Getting Access through JWT
* Create a user via the /api/users/ endpoint.
* Obtain an access token via the /api/users/token endpoint.

## Swagger Documentation
Access the API documentation at 

```shell
/api/doc/swagger
```