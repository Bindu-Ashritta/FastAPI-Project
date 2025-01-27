# Project Documentation

## Project Overview
This project is a FastAPI-based application that integrates Google OAuth2 for user authentication and allows users to manage a watchlist. The watchlist includes operations such as creating, updating, retrieving, and deleting entries. The application also includes a secure token-based authentication system.

## Dependencies

### Python Libraries

-fastapi: For building the web framework.

-Installation: pip install fastapi

-uvicorn: For running the FastAPI application.

-Installation: pip install uvicorn

-python-dotenv: To load environment variables from a .env file.

-Installation: pip install python-dotenv

-authlib: For integrating OAuth2 with Google.

-Installation: pip install authlib

-SQLAlchemy: For database ORM.

-Installation: pip install sqlalchemy

-pydantic: For data validation and serialization.

-Installation: pip install pydantic

-jinja2: For rendering templates.

-Installation: pip install jinja2

Additional Requirements

Python 3.8 or later



## Project Setup

Step 1: Set Up Virtual Environment

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

Step 2: Install Dependencies

pip install -r requirements.txt

Step 3: Configure Environment Variables 

Create a .env file in the project root.

Add the following keys:

CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
REDIRECT_URI=http://localhost:8000/auth

Step 5: Run the Application

Use the following command to run the application:

uvicorn main:app --reload

The application will be available at http://localhost:8000.


### Usage Instructions

-Usage Instructions

####Authentication

Login: Navigate to /login to log in with Google OAuth2.

Logout: Use the /logout endpoint to clear the session.

####Watchlist Management

Create Watchlist: Use the /watchlists/ POST endpoint with symbol and list_name parameters.

Retrieve Watchlist: Use the /watchlists/ GET endpoint to list all watchlist entries for the authenticated user.

Retrieve Specific Entry: Use the /watchlists/{id} GET endpoint to get a specific watchlist entry by ID.

Update Watchlist: Use the /watchlists/{id} PUT endpoint to update an entry.

Delete Watchlist: Use the /watchlists/{id} DELETE endpoint to delete an entry.