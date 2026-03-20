from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from models.db import get_db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # 1. Room Stats
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Available'")
    available_rooms = cursor.fetchone()[0]
    
    room_stats = {'total': total_rooms, 'available': available_rooms}
    
    # 2. Active Bookings
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status IN ('Confirmed', 'Checked-In')")
    active_bookings = cursor.fetchone()[0]
    
    # 3. Today's Check-ins (Using Python's datetime to get today's date)
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT b.id, c.full_name, r.room_number, b.status 
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.check_in_date = ?
    """, (today_str,))
    
    columns = [column[0] for column in cursor.description]
    todays_checkins = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # 4. Revenue for Last 7 Days (Calculating daily income)
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    revenue_data = []
    for d in dates:
        cursor.execute("""
            SELECT SUM(r.price) FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            WHERE ? >= b.check_in_date AND ? < b.check_out_date 
            AND b.status IN ('Confirmed', 'Checked-In', 'Completed')
        """, (d, d))
        rev = cursor.fetchone()[0]
        revenue_data.append(round(rev, 2) if rev else 0)
        
    # Create clean labels for the chart (e.g., 'Mar 15')
    chart_labels = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]

    return render_template('dashboard/dashboard.html', 
                           room_stats=room_stats, 
                           active_bookings=active_bookings,
                           todays_checkins=todays_checkins,
                           revenue_data=revenue_data,
                           chart_labels=chart_labels)
@dashboard_bp.route('/api/v1/stats')
def api_stats():
    """RESTful API Endpoint returning pure JSON data for mobile app integration."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'")
    upcoming = cursor.fetchone()[0]
    
    return jsonify({
        "system": "HMS API v1",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "data": {
            "total_rooms": total_rooms,
            "upcoming_checkins": upcoming
        }
    })