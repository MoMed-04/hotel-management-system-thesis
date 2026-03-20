import sqlite3
from flask import g
from config import DATABASE_PATH

def get_db():
    """Opens a new database connection if there is none yet for the current request."""
    # 'g' is a special Flask object that stores data globally during a single user request
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        # This tells SQLite to return rows that behave like dictionaries, which is much easier to work with!
        g.db.row_factory = sqlite3.Row 
    return g.db

def close_db(e=None):
    """Safely closes the database connection when the request is finished."""
    db = g.pop('db', None)
    if db is not None:
        db.close()