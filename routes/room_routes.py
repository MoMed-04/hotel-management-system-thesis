from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.room_model import add_room, delete_room
from models.db import get_db
from datetime import datetime

room_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

@room_bp.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # LEFT JOIN to check if the room has an active booking today
    cursor.execute("""
        SELECT r.id, r.room_number, r.room_type, r.price, b.status
        FROM rooms r
        LEFT JOIN bookings b 
            ON r.id = b.room_id 
            AND ? >= b.check_in_date 
            AND ? < b.check_out_date
            AND b.status IN ('Confirmed', 'Checked-In')
        ORDER BY r.room_number ASC
    """, (today, today))
    
    rooms_data = cursor.fetchall()
    rooms = []
    
    for r in rooms_data:
        booking_status = r[4] # This gets the 'status' column from the bookings table
        
        # Calculate real-time status based on teacher's rules
        calculated_status = 'Vacant'
        if booking_status == 'Confirmed':
            calculated_status = 'Booked'
        elif booking_status == 'Checked-In':
            calculated_status = 'Checked In'
            
        rooms.append({
            'id': r[0],
            'room_number': r[1],
            'room_type': r[2],
            'price': r[3],
            'status': calculated_status
        })

    return render_template('rooms/rooms_list.html', rooms=rooms)

@room_bp.route('/add', methods=['POST'])
def create():
    # Grab data from the HTML form
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    
    # Try to add it to the database
    add_room(room_number, room_type, price)
    
    return redirect(url_for('rooms.index'))

@room_bp.route('/delete/<int:room_id>', methods=['POST'])
def delete(room_id):
    delete_room(room_id)
    return redirect(url_for('rooms.index'))