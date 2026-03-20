from models.db import get_db

def get_all_customers():
    """Fetches a list of all registered customers."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY full_name ASC")
    return cursor.fetchall()

def add_customer(full_name, phone, email):
    """Inserts a new customer into the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO customers (full_name, phone, email) VALUES (?, ?, ?)",
        (full_name, phone, email)
    )
    db.commit()
    return True