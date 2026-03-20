from models.db import get_db

def get_active_booking_count():
    """Fetches the total number of active/confirmed bookings."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as active_count FROM bookings WHERE status IN ('Confirmed', 'Checked-In')")
    result = cursor.fetchone()
    return result['active_count']

def get_all_bookings():
    """Fetches all bookings, joining customer and room data so we can see names instead of just IDs."""
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT b.id, c.full_name, r.room_number, b.check_in_date, b.check_out_date, b.status 
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        ORDER BY b.check_in_date DESC
    """
    cursor.execute(query)
    return cursor.fetchall()

def is_room_available(room_id, check_in_date, check_out_date):
    """
    THESIS ALGORITHM: The Universal Overlap Check.
    Returns True if the room is available, False if there is a double booking.
    """
    db = get_db()
    cursor = db.cursor()
    
    # We check if check_in < requested_check_out AND check_out > requested_check_in
    query = """
        SELECT COUNT(*) as overlapping
        FROM bookings
        WHERE room_id = ? 
        AND status IN ('Confirmed', 'Checked-In')
        AND check_in_date < ? 
        AND check_out_date > ?
    """
    # Notice we pass the requested dates in the opposite order to match the query logic!
    cursor.execute(query, (room_id, check_out_date, check_in_date))
    result = cursor.fetchone()
    
    # If overlapping is 0, it evaluates to True (Available!)
    return result['overlapping'] == 0

def create_booking(customer_id, room_id, check_in_date, check_out_date):
    """Saves the reservation to the database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO bookings (customer_id, room_id, check_in_date, check_out_date) VALUES (?, ?, ?, ?)",
        (customer_id, room_id, check_in_date, check_out_date)
    )
    db.commit()
    return True
def update_booking_status(booking_id, new_status):
    """
    Updates a booking's status AND automatically updates the associated room's status.
    This ensures our database remains consistent.
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. Update the booking status
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
    
    # 2. Find out which room is attached to this booking
    cursor.execute("SELECT room_id FROM bookings WHERE id = ?", (booking_id,))
    result = cursor.fetchone()
    
    if result:
        room_id = result['room_id']
        # 3. Automatically update the room's physical status
        if new_status == 'Checked-In':
            cursor.execute("UPDATE rooms SET status = 'Occupied' WHERE id = ?", (room_id,))
        elif new_status == 'Completed' or new_status == 'Cancelled':
            cursor.execute("UPDATE rooms SET status = 'Available' WHERE id = ?", (room_id,))
            
    db.commit()
    return True
def get_booking_by_id(booking_id):
    """Fetches a single booking with all related guest and room details for the invoice."""
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT b.id, c.full_name, c.phone, c.email, 
               r.room_number, r.room_type, r.price, 
               b.check_in_date, b.check_out_date, b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.id = ?
    """
    cursor.execute(query, (booking_id,))
    return cursor.fetchone()