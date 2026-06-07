import os
import re
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from models.db import get_db
import traceback

# Setup VPN Proxy for local testing only
if 'PYTHONANYWHERE_DOMAIN' not in os.environ:
    os.environ['http_proxy'] = 'http://127.0.0.1:7897'
    os.environ['https_proxy'] = 'http://127.0.0.1:7897'

guest_bp = Blueprint('guest', __name__, url_prefix='/guest')

# --- Standard Routes ---
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
# 1. BOOKING API
# ==========================================
@guest_bp.route('/api/book_room', methods=['POST'])
def api_book_room():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    user_id = session.get('user_id')
    db_room_type = data.get('room_type', 'Single')
    check_in = data.get('in')
    check_out = data.get('out')

    try:
        db = get_db()
        cursor = db.cursor()

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
# 2. REFUND API
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


# ==========================================
# 3. SEARCH ROOMS API
# ==========================================
@guest_bp.route('/api/search_rooms', methods=['POST'])
def api_search_rooms():
    data = request.json
    check_in = data.get('in')
    check_out = data.get('out')

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT room_type, COUNT(*) as available_count,
                   MIN(price) as price
            FROM rooms
            WHERE id NOT IN (
                SELECT room_id FROM bookings
                WHERE (status IS NULL OR status NOT IN ('Refunded', 'Cancelled'))
                AND (check_in_date < ? AND check_out_date > ?)
            )
            GROUP BY room_type
        """, (check_out, check_in))

        rooms = cursor.fetchall()
        result = [{'room_type': r[0], 'available': r[1], 'price': r[2]} for r in rooms]
        return jsonify({'success': True, 'rooms': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# 4. RULE-BASED AI & ADMIN LOGGER API (Fully Fixed)
# ==========================================
@guest_bp.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    original_message = data.get('message', '')
    
    # Break sentence into words
    words = re.findall(r'\w+', original_message.lower())
    
    username = session.get('username', 'Guest')
    user_id = session.get('user_id')

    # --- 1. THE SMART LOGIC TREE ---
    
    # FIX: Only say hello if the entire message is 3 words or less.
    if len(words) <= 3 and any(w in words for w in ['hi', 'hello', 'hey']):
        reply = f"Hello {username}! I am the SaaS Hotel Assistant. How can I help you today?"
        
    elif 'room' in words and any(w in words for w in ['left', 'available', 'price', 'cost', 'much', 'rooms']):
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT room_type, MIN(price) as price FROM rooms GROUP BY room_type")
            rooms = cursor.fetchall()
            room_info = ", ".join([f"{r[0]}s from ${r[1]}" for r in rooms])
            reply = f"We currently have {room_info} available! Please check the Search tab for exact dates."
        except:
            reply = "We have multiple room types available! Please check the 'Search' tab."
            
    elif any(w in words for w in ['book', 'reserve']):
        reply = "To book a room, please click the 'Hotel / Room Search' tab at the top of your dashboard."
        
    elif any(w in words for w in ['wifi', 'internet', 'password']):
        reply = "Our free WiFi network is 'SaaS_Guest' and the password is 'Stay2026'."
        
    elif any(w in words for w in ['time', 'checkin', 'checkout', 'check']):
        reply = "Check-in time is 2:00 PM and Check-out is at 12:00 PM noon."
        
    else:
        reply = "I don't have the exact answer for that. Please wait for the human assistant, they are not online right now. Your message has been recorded."

    # --- 2. SAVE TO DATABASE FOR ADMIN TO SEE ---
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                guest_message TEXT,
                bot_reply TEXT,
                status TEXT DEFAULT 'Unread',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO chat_logs (user_id, username, guest_message, bot_reply)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, original_message, reply))
        
        db.commit()
    except Exception as e:
        print(f"Chat Log DB Error: {e}")

    return jsonify({'success': True, 'reply': reply})


# ==========================================
# 5. GET GUEST'S BOOKED ROOMS
# ==========================================
@guest_bp.route('/api/my_rooms', methods=['GET'])
def api_my_rooms():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    user_id = session.get('user_id')

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT DISTINCT r.id, r.room_number, r.room_type
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN customers c ON b.customer_id = c.id
            WHERE c.user_id = ?
            AND b.status = 'Confirmed'
        """, (user_id,))

        rooms = cursor.fetchall()
        result = [{'id': r[0], 'room_number': r[1], 'room_type': r[2]} for r in rooms]
        return jsonify({'success': True, 'rooms': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# 6. SUBMIT REVIEW API
# ==========================================
@guest_bp.route('/api/submit_review', methods=['POST'])
def api_submit_review():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    user_id = session.get('user_id')
    username = session.get('username', 'Guest')
    room_id = data.get('room_id')
    stars = data.get('stars')
    review_text = data.get('review')

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO reviews (user_id, room_id, username, stars, review_text)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, room_id, username, stars, review_text))

        db.commit()
        return jsonify({'success': True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# 7. GET ALL REVIEWS
# ==========================================
@guest_bp.route('/api/get_reviews', methods=['GET'])
def api_get_reviews():
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT rv.username, rv.stars, rv.review_text, r.room_type
            FROM reviews rv
            JOIN rooms r ON rv.room_id = r.id
            ORDER BY rv.id DESC
            LIMIT 20
        """)

        reviews = cursor.fetchall()
        result = [{'username': r[0], 'stars': r[1], 'review': r[2], 'room_type': r[3]} for r in reviews]
        return jsonify({'success': True, 'reviews': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# 8. GUEST TICKETS (Support History)
# ==========================================
@guest_bp.route('/tickets')
def tickets():
    return render_template('guest/guest_tickets.html')

@guest_bp.route('/api/my_tickets', methods=['GET'])
def api_my_tickets():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    user_id = session.get('user_id')

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT guest_message, bot_reply, status, datetime(created_at, 'localtime')
            FROM chat_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))

        logs = cursor.fetchall()
        tickets_data = [{'message': r[0], 'reply': r[1], 'status': r[2], 'time': r[3]} for r in logs]
        
        return jsonify({'success': True, 'tickets': tickets_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    # ==========================================
# 9. UPDATE GUEST PROFILE
# ==========================================
@guest_bp.route('/api/update_profile', methods=['POST'])
def api_update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.json
    user_id = session.get('user_id')
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')

    try:
        db = get_db()
        cursor = db.cursor()
        
        # Update the customer record linked to this user account
        cursor.execute("""
            UPDATE customers 
            SET full_name = ?, email = ?, phone = ?
            WHERE user_id = ?
        """, (full_name, email, phone, user_id))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500