from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.room_model import get_all_rooms, add_room, delete_room

room_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

@room_bp.route('/')
def index():
    rooms = get_all_rooms()
    return render_template('rooms/rooms_list.html', rooms=rooms)

@room_bp.route('/add', methods=['POST'])
def create():
    # Grab data from the HTML form
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    price = request.form.get('price')
    
    # Try to add it to the database
    success = add_room(room_number, room_type, price)
    
    return redirect(url_for('rooms.index'))

@room_bp.route('/delete/<int:room_id>', methods=['POST'])
def delete(room_id):
    delete_room(room_id)
    return redirect(url_for('rooms.index'))