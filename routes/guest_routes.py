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
# 4. AI CHAT API (Powered by Gemini)
# ==========================================
@guest_bp.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    message = data.get('message', '')
    username = session.get('username', 'Guest')

    try:
        db = get_db()
        cursor = db.cursor()

        # THE RAG SYSTEM: Pulling live data from your database!
        cursor.execute("SELECT room_type, COUNT(*) as total, MIN(price) as price FROM rooms GROUP BY room_type")
        rooms = cursor.fetchall()
        room_info = "\n".join([f"- {r[0]}: {r[1]} total rooms. Starting at ${r[2]}/night" for r in rooms])

        import urllib.request
        import urllib.error
        import json as jsonlib
        import ssl 

        # 🚨 PASTE YOUR REAL KEY HERE 🚨
        api_key = 'PASTE_YOUR_REAL_KEY_HERE'

        system_context = f"""You are an exclusive, intelligent front desk assistant for our hotel. 
The guest's name is {username}. Always greet them by name.

STRICT INSTRUCTIONS:
1. NEVER hallucinate or make up room types. You must ONLY use the following live database information:
{room_info}
2. If the guest asks how to book a room, tell them to "Please click the 'Hotel / Room Search' tab at the top of your dashboard to check live dates and book instantly."
3. Hotel Policies: Check-in is 2:00 PM, Check-out is 12:00 PM. Free WiFi (Network: SaaS_Guest, Pass: Stay2026).
4. Keep your response under 3 short sentences. Be polite and concise.

Guest message: """

        payload = jsonlib.dumps({
            "contents": [
                {
                    "parts": [
                        {"text": system_context + message}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 150,
                "temperature": 0.3
            }
        }).encode('utf-8')

        # 🚨 THE ONLY FIX WE NEEDED: 🚨
        # Swapped to gemini-2.5-flash (The active 2026 model!)
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': api_key
            }
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            result = jsonlib.loads(response.read().decode('utf-8'))
            reply = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'success': True, 'reply': reply})

    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            google_error = jsonlib.loads(err_msg)
            exact_reason = google_error.get('error', {}).get('message', 'Unknown API Error')
        except:
            exact_reason = "Invalid Key or Payload"
        return jsonify({'success': False, 'error': f"Google Error: {exact_reason}"}), 500
        
    except urllib.error.URLError as e:
        return jsonify({'success': False, 'error': f"Network Blocked: {e.reason}. (Check VPN!)"}), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"System Error: {repr(e)}"}), 500


# ==========================================
# 5. GET GUEST'S BOOKED ROOMS (for reviews)
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