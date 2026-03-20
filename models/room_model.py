from models.db import get_db

def get_room_stats():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM rooms")
    total_rooms = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as available FROM rooms WHERE status = 'Available'")
    available_rooms = cursor.fetchone()['available']
    return {'total': total_rooms, 'available': available_rooms}

def get_all_rooms():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM rooms ORDER BY room_number ASC")
    return cursor.fetchall()

# --- NEW FUNCTIONS BELOW ---

def add_room(room_number, room_type, price):
    """Inserts a new room into the database."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO rooms (room_number, room_type, price) VALUES (?, ?, ?)",
            (room_number, room_type, price)
        )
        db.commit()
        return True
    except:
        # If the room number already exists, it will trigger an exception
        return False

def delete_room(room_id):
    """Deletes a room by its ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    db.commit()