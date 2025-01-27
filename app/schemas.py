from pydantic import BaseModel
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    google_oauth_id: Optional[str] = None

    class Config:
        orm_mode = True

class WatchlistBase(BaseModel):
    symbol: str
    list_name: str

class WatchlistCreate(WatchlistBase):
    pass

class Watchlist(WatchlistBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True