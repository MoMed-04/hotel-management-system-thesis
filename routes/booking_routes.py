from flask import Blueprint, render_template, request, redirect, url_for, Response
from datetime import datetime
from models.booking_model import get_all_bookings, is_room_available, create_booking, update_booking_status, get_booking_by_id
from models.customer_model import get_all_customers
from models.room_model import get_all_rooms

booking_bp = Blueprint('bookings', __name__, url_prefix='/bookings')

@booking_bp.route('/')
def index():
    bookings = get_all_bookings()
    return render_template('bookings/bookings_list.html', bookings=bookings)

@booking_bp.route('/add', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        room_id = request.form.get('room_id')
        check_in = request.form.get('check_in_date')
        check_out = request.form.get('check_out_date')

        # 1. Ask the algorithm if the room is safe to book
        if is_room_available(room_id, check_in, check_out):
            # 2. It is safe! Create the booking.
            create_booking(customer_id, room_id, check_in, check_out)
            return redirect(url_for('bookings.index'))
        else:
            # 3. Danger! Double booking detected. Reload page with error.
            customers = get_all_customers()
            rooms = get_all_rooms()
            error_msg = "Error: This room is already booked during those dates. Please select different dates or a different room."
            return render_template('bookings/new_booking.html', customers=customers, rooms=rooms, error=error_msg)

    # If it's just a GET request, display the blank form
    customers = get_all_customers()
    rooms = get_all_rooms()
    return render_template('bookings/new_booking.html', customers=customers, rooms=rooms)
@booking_bp.route('/<int:booking_id>/status/<new_status>', methods=['POST'])
def change_status(booking_id, new_status):
    # Security check to ensure only valid statuses are processed
    valid_statuses = ['Checked-In', 'Completed', 'Cancelled']
    if new_status in valid_statuses:
        update_booking_status(booking_id, new_status)
    
    return redirect(url_for('bookings.index'))
@booking_bp.route('/<int:booking_id>/invoice')
def generate_invoice(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return "Booking not found", 404

    # Calculate the total number of nights using Python's datetime
    check_in = datetime.strptime(booking['check_in_date'], '%Y-%m-%d')
    check_out = datetime.strptime(booking['check_out_date'], '%Y-%m-%d')
    nights = (check_out - check_in).days
    
    # Ensure they are charged for at least 1 night
    if nights <= 0:
        nights = 1 

    total_amount = nights * booking['price']

    return render_template('bookings/invoice.html', booking=booking, nights=nights, total_amount=total_amount)
@booking_bp.route('/export-csv')
def export_csv():
    """Generates a downloadable CSV report of all bookings."""
    bookings = get_all_bookings()
    
    def generate():
        # CSV Header
        yield 'ID,Guest Name,Room Number,Check-In,Check-Out,Status\n'
        # CSV Data Rows
        for b in bookings:
            yield f"{b['id']},{b['full_name']},{b['room_number']},{b['check_in_date']},{b['check_out_date']},{b['status']}\n"

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=hotel_bookings_report.csv"})