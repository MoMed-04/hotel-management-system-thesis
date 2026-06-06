import sqlite3
from models.db import get_db

def get_user_by_username(username):
    """Fetches a user record by their username."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()

def create_new_user(username, password_hash, role='Guest'):
    """Inserts a brand new user into the database securely."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
            (username, password_hash, role)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        # This safely catches the error if someone tries to register a username that already exists
        return False