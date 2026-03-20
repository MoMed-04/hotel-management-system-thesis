from flask import Flask, session, redirect, url_for, request
from config import SECRET_KEY
from models.db import close_db
from translations import TRANSLATIONS

from routes.dashboard_routes import dashboard_bp
from routes.room_routes import room_bp
from routes.customer_routes import customer_bp
from routes.booking_routes import booking_bp
from routes.auth_routes import auth_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.teardown_appcontext(close_db)

app.register_blueprint(dashboard_bp)
app.register_blueprint(room_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(auth_bp)

# --- THESIS FEATURE: Custom Translation Engine ---
@app.route('/set_lang/<lang>')
def set_lang(lang):
    """Saves the chosen language to the user's secure session."""
    if lang in ['en', 'zh']:
        session['lang'] = lang
    # Send them back to exactly where they were
    return redirect(request.referrer or url_for('dashboard.index'))

@app.context_processor
def inject_translator():
    """Injects the 't' function into all HTML files to translate text instantly."""
    def translate(text):
        lang = session.get('lang', 'en') # Default to English
        return TRANSLATIONS.get(lang, {}).get(text, text)
    return dict(t=translate)
# -------------------------------------------------

@app.before_request
def require_login():
    """Kicks unauthenticated users back to the login screen."""
    allowed_routes = ['auth.login', 'static', 'set_lang']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)