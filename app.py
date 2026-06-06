from flask import Flask, session, redirect, url_for, request
from config import SECRET_KEY
from models.db import close_db
from translations import TRANSLATIONS

# --- ADMIN BLUEPRINTS ---
from routes.dashboard_routes import dashboard_bp
from routes.room_routes import room_bp
from routes.customer_routes import customer_bp
from routes.booking_routes import booking_bp
from routes.auth_routes import auth_bp

# --- NEW GUEST BLUEPRINT ---
from routes.guest_routes import guest_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.teardown_appcontext(close_db)

# Register Admin Routes
app.register_blueprint(dashboard_bp)
app.register_blueprint(room_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(auth_bp)

# Register Guest Routes
app.register_blueprint(guest_bp)

# --- THESIS FEATURE: Custom Translation Engine ---
@app.route('/set_lang/<lang>')
def set_lang(lang):
    """Saves the chosen language to the user's secure session."""
    if lang in ['en', 'zh']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard.index'))

@app.context_processor
def inject_translator():
    """Injects the 't' function into all HTML files to translate text instantly."""
    def translate(text):
        lang = session.get('lang', 'en') 
        return TRANSLATIONS.get(lang, {}).get(text, text)
    return dict(t=translate)
# -------------------------------------------------

@app.before_request
def check_permissions():
    """Handles Security: Kicks unauthenticated users out, and separates Admin/Guest access."""
    # 1. Allow static files (CSS/JS) to load naturally
    if request.endpoint and request.endpoint.startswith('static'):
        return

    # 2. Public routes that ANYONE can access without logging in
    public_routes = ['auth.login', 'auth.register', 'set_lang', 'guest.search', 'guest.room_details']
    if request.endpoint in public_routes:
        return

    # 3. If they aren't logged in, send them to login
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 4. If they ARE a Guest, block them from Admin pages
    is_admin_route = request.endpoint and not request.endpoint.startswith('guest.') and not request.endpoint.startswith('auth.')
    
    if session.get('role') == 'Guest' and is_admin_route:
        # NEW: If a guest accidentally goes to the root URL "/", gracefully redirect them to their portal
        if request.path == '/':
            return redirect(url_for('guest.search'))
            
        # Otherwise, if they try to hack into /admin/orders, throw the security wall
        return "403 Forbidden: Administrator access required to view this module.", 403

# ==========================================
# IGNITION KEY - MUST BE AT THE VERY BOTTOM
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)