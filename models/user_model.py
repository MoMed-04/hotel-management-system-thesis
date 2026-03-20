from models.db import get_db

def get_user_by_username(username):
    """Fetches a user record by their username."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()