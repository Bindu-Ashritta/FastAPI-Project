from sqlalchemy.orm import Session
from . import models, schemas

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_watchlist(db: Session, user_id: int, symbol: str, list_name: str):
    watchlist_entry = models.Watchlist(user_id=user_id, symbol=symbol, list_name=list_name)
    db.add(watchlist_entry)
    db.commit()
    db.refresh(watchlist_entry)
    return watchlist_entry

def get_watchlist_by_user_id(db: Session, user_id: int):
    return db.query(models.Watchlist).filter(models.Watchlist.user_id == user_id).all()

def get_watchlist_by_id(db: Session, id: int):
    return db.query(models.Watchlist).filter(models.Watchlist.id == id).first()

def update_watchlist(db: Session, id: int, symbol: str, list_name: str):
    watchlist_entry = get_watchlist_by_id(db, id)
    if watchlist_entry:
        watchlist_entry.symbol = symbol
        watchlist_entry.list_name = list_name
        db.commit()
        db.refresh(watchlist_entry)
        return watchlist_entry
    return None

def delete_watchlist(db: Session, id: int):
    watchlist_entry = get_watchlist_by_id(db, id)
    if watchlist_entry:
        db.delete(watchlist_entry)
        db.commit()
        return watchlist_entry
    return None