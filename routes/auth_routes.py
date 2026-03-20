from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models.user_model import get_user_by_username

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 1. Look up the user in the database
        user = get_user_by_username(username)
        
        # 2. Check if user exists AND the password matches the hash
        if user and check_password_hash(user['password_hash'], password):
            # 3. Success! Save their info in the secure session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard.index'))
        else:
            error = "Invalid username or password."

    return render_template('auth/login.html', error=error)

@auth_bp.route('/logout')
def logout():
    # Clear the session to log them out
    session.clear()
    return redirect(url_for('auth.login'))