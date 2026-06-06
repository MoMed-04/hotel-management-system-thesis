from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from models.db import get_db
import traceback

guest_bp = Blueprint('guest', __name__, url_prefix='/guest')

@guest_bp.route('/')
@guest_bp.route('/search')
def search():
    return render_template('guest/guest_search.html')

@guest_bp.route('/room/<int:room_id>')
def room_details(room_id):
    return render_template('guest/room_details.html', room_id=room_id)

@guest_bp.route('/book', methods=['POST'])
def online_booking():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('guest.orders'))

@guest_bp.route('/orders')
def orders():
    return render_template('guest/guest_orders.html')

@guest_bp.route('/account')
def account():
    return render_template('guest/guest_account.html')

@guest_bp.route('/chat')
def chat():
    return render_template('guest/guest_chat.html')

@guest_bp.route('/reviews')
def reviews():
    return render_template('guest/guest_reviews.html')


# ==========================================
# 1. BOOKING API (Immune to Translation Bugs)
# ==========================================
@guest_bp.route('/api/book_room', methods=['POST'])
def api_book_room():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    user_id = session.get('user_id')
    
    # NEW: We strictly pull the backend code instead of the translated UI text
    db_room_type = data.get('room_type', 'Single')
    check_in = data.get('in')
    check_out = data.get('out')
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # --- FIND OR CREATE CUSTOMER ---
        cursor.execute("SELECT id FROM customers WHERE user_id = ?", (user_id,))
        customer = cursor.fetchone()
        
        if customer:
            try: customer_id = customer['id']
            except TypeError: customer_id = customer[0]
        else:
            username = session.get('username', 'Online Guest')
            cursor.execute("""
                INSERT INTO customers (user_id, full_name, phone, email) 
                VALUES (?, ?, 'N/A', 'N/A')
            """, (user_id, username))
            customer_id = cursor.lastrowid
            
        # --- BULLETPROOF OVERLAP ALGORITHM ---
        cursor.execute("""
            SELECT id FROM rooms 
            WHERE room_type = ? 
            AND id NOT IN (
                SELECT room_id FROM bookings 
                WHERE (status IS NULL OR status NOT IN ('Refunded', 'Cancelled'))
                AND (check_in_date < ? AND check_out_date > ?)
            )
            LIMIT 1
        """, (db_room_type, check_out, check_in))
        
        room = cursor.fetchone()
        if room:
            try: room_id = room['id']
            except TypeError: room_id = room[0]
        else:
            return jsonify({'success': False, 'error': f'Sold Out! No {db_room_type} rooms are available for these dates.'}), 400
            
        # --- INSERT AND GRAB REAL ID ---
        cursor.execute("""
            INSERT INTO bookings (customer_id, room_id, check_in_date, check_out_date, status)
            VALUES (?, ?, ?, ?, 'Confirmed')
        """, (customer_id, room_id, check_in, check_out))
        
        real_booking_id = cursor.lastrowid 
        
        db.commit()
        return jsonify({'success': True, 'message': 'Saved!', 'real_id': real_booking_id})
    
    except Exception as e:
        print("====== DATABASE CROSSOVER ERROR ======")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# 2. REFUND API (Connects Frontend to Admin)
# ==========================================
@guest_bp.route('/api/refund_booking', methods=['POST'])
def api_refund_booking():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    real_booking_id = data.get('real_id')

    if not real_booking_id:
        return jsonify({'success': False, 'error': 'Missing booking ID'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE bookings 
            SET status = 'Refunded' 
            WHERE id = ?
        """, (real_booking_id,))
        
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        print("====== DATABASE REFUND ERROR ======")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500