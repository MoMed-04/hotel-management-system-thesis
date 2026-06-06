from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from models.db import get_db
from datetime import datetime, timedelta
import shutil
import os
from werkzeug.security import generate_password_hash

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Available'")
    available_rooms = cursor.fetchone()[0]
    room_stats = {'total': total_rooms, 'available': available_rooms}
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status IN ('Confirmed', 'Checked-In')")
    active_bookings = cursor.fetchone()[0]
    
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
        
    chart_labels = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]

    return render_template('dashboard/dashboard.html', 
                           room_stats=room_stats, active_bookings=active_bookings,
                           todays_checkins=todays_checkins, revenue_data=revenue_data, chart_labels=chart_labels)

@dashboard_bp.route('/api/v1/stats')
def api_stats():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'")
    upcoming = cursor.fetchone()[0]
    return jsonify({"system": "HMS API v1", "timestamp": datetime.now().isoformat(), "status": "success", "data": {"total_rooms": total_rooms, "upcoming_checkins": upcoming}})

# ==========================================
# STAFF MANAGEMENT DASHBOARD ROUTES
# ==========================================
@dashboard_bp.route('/staff')
def staff():
    if session.get('role') == 'Guest':
        return redirect(url_for('guest.search'))
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE role IN ('Admin', 'Staff')")
    columns = [column[0] for column in cursor.description]
    staff_members = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('dashboard/staff.html', staff_members=staff_members)

@dashboard_bp.route('/api/staff/add', methods=['POST'])
def add_staff():
    if session.get('role') != 'Admin': return jsonify({'success': False, 'error': 'Only Admins can add staff.'}), 403
    data = request.json
    try:
        db = get_db()
        cursor = db.cursor()
        hashed_pw = generate_password_hash(data['password'])
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (data['username'], hashed_pw, data['role']))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/staff/edit', methods=['POST'])
def edit_staff():
    if session.get('role') != 'Admin': return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.json
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (data['role'], data['id']))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/staff/delete', methods=['POST'])
def delete_staff():
    if session.get('role') != 'Admin': return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.json
    if data['id'] == session.get('user_id'): return jsonify({'success': False, 'error': 'You cannot delete yourself!'}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (data['id'],))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# SETTINGS & BACKUP ROUTES
# ==========================================
@dashboard_bp.route('/settings')
def settings():
    if session.get('role') != 'Admin': return redirect(url_for('dashboard.index'))
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/api/backup', methods=['POST'])
def backup_database():
    if session.get('role') != 'Admin': return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.db"
        shutil.copy2('database.db', backup_filename)
        return jsonify({'success': True, 'filename': backup_filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/settings/save', methods=['POST'])
def save_settings():
    if session.get('role') != 'Admin': return jsonify({'success': False}), 403
    return jsonify({'success': True})