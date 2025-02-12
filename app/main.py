from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from app import schemas
from .config import CLIENT_ID, CLIENT_SECRET, SECRET_KEY, REDIRECT_URI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import get_db, engine
from . import crud, models
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowAuthorizationCode
from fastapi.openapi.models import SecurityScheme as SecuritySchemeModel
import secrets

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 bearer token for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Middleware setup with the generated secret key
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# OAuth setup with Google
oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={'scope': 'openid email profile', 'redirect_uri': REDIRECT_URI}
)

models.Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.DEBUG)

# Utility function to fake password hashing
def fake_hash_password(password: str):
    return "fakehashed" + password

# Pydantic model for the token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Pydantic model for the user
class User(BaseModel):
    username: str
    email: str
    google_oauth_id: Optional[str] = None

# Pydantic model for the user in the database
class UserInDB(User):
    hashed_password: str

# Function to get a user from the database
def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Function to authenticate the user
def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not user.hashed_password == fake_hash_password(password):
        return False
    return user


def verify_token_and_get_user_info(token: str):
    try:
        # Example using authlib and Google OAuth
        credentials = oauth.google.parse_id_token(token)
        if credentials:
            return credentials
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_from_token(db: Session, token: str):
    user_info = verify_token_and_get_user_info(token)
    # You can then query your DB based on user_info['email'] or other identifier
    user = crud.get_user_by_email(db, user_info['email'])
    return user

# Route Definitions

@app.get("/")
def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('welcome')
    return templates.TemplateResponse("home.html", {"request": request})

@app.get('/welcome')
def welcome(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse('login')
    return templates.TemplateResponse('welcome.html', {'request': request, 'user': user})

@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session['state'] = state
    logging.debug(f"Generated state: {state}")
    url = request.url_for('auth')
    logging.debug(f"Redirecting to: {url}")
    return await oauth.google.authorize_redirect(request, url, state=state, prompt='consent')

@app.get('/auth')
async def auth(request: Request):
    stored_state = request.session.get('state')
    received_state = request.query_params.get('state')
    logging.debug(f"Stored state: {stored_state}")
    logging.debug(f"Received state: {received_state}")
    if stored_state != received_state:
        logging.error("Mismatching state")
        raise HTTPException(status_code=400, detail="Mismatching state")
    try:
        token = await oauth.google.authorize_access_token(request)
        logging.debug(f"Received token: {token}")
    except OAuthError as e:
        logging.error(f"OAuthError: {e.error}")
        return templates.TemplateResponse('error.html', {'request': request, 'error': e.error})
    user = token.get('userinfo')
    if user:
        request.session['user'] = dict(user)
        request.session['token'] = token['access_token']
        # Save user to the database if not already present
        db = next(get_db())
        existing_user = crud.get_user_by_email(db, user['email'])
        if not existing_user:
            new_user = models.User(
                username=user['email'],
                email=user['email'],
                google_oauth_id=user.get('sub'),  # Use the 'sub' field from the token as the Google OAuth ID
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
    return RedirectResponse('welcome')

@app.get('/logout')
def logout(request: Request):
    request.session.pop('user', None)
    request.session.pop('token', None)
    return RedirectResponse('/')

@app.post("/watchlists/")
def create_watchlist(symbol: str, list_name: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.debug(f"Token received: {token}")
    user = get_user_from_token(db, token)
    if user:
        watchlist_entry = crud.create_watchlist(db, user.id, symbol, list_name)
        return watchlist_entry
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/watchlists/", response_model=List[schemas.Watchlist])
def list_watchlist(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.debug(f"Token received: {token}")
    user = get_user_from_token(db, token)
    if user:
        watchlist_entries = crud.get_watchlist_by_user_id(db, user.id)
        return watchlist_entries
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/watchlists/{id}", response_model=schemas.Watchlist)
def get_watchlist_entry(id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.debug(f"Token received: {token}")
    user = get_user_from_token(db, token)
    if user:
        watchlist_entry = crud.get_watchlist_by_id(db, id)
        if watchlist_entry and watchlist_entry.user_id == user.id:
            return watchlist_entry
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.put("/watchlists/{id}", response_model=schemas.Watchlist)
def update_watchlist_entry(id: int, symbol: str, list_name: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.debug(f"Token received: {token}")
    user = get_user_from_token(db, token)
    if user:
        watchlist_entry = crud.get_watchlist_by_id(db, id)
        if watchlist_entry and watchlist_entry.user_id == user.id:
            updated_entry = crud.update_watchlist(db, id, symbol, list_name)
            return updated_entry
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.delete("/watchlists/{id}", response_model=schemas.Watchlist)
def delete_watchlist_entry(id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.debug(f"Token received: {token}")
    user = get_user_from_token(db, token)
    if user:
        watchlist_entry = crud.get_watchlist_by_id(db, id)
        if watchlist_entry and watchlist_entry.user_id == user.id:
            deleted_entry = crud.delete_watchlist(db, id)
            return deleted_entry
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    raise HTTPException(status_code=401, detail="Not authenticated")

# Add OAuth2 security scheme to OpenAPI schema
@app.on_event("startup")
async def startup_event():
    openapi_schema = app.openapi()
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2AuthorizationCodeBearer": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                    "tokenUrl": "https://oauth2.googleapis.com/token",
                    "scopes": {
                        "openid": "OpenID Connect scope",
                        "email": "Access to your email",
                        "profile": "Access to your profile"
                    }
                }
            }
        }
    }
    openapi_schema["security"] = [{"OAuth2AuthorizationCodeBearer": []}]
    app.openapi_schema = openapi_schema