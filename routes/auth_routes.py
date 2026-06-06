from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
# NEW: Imported the create_new_user function you just added!
from models.user_model import get_user_by_username, create_new_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        selected_role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            db_role = user['role']
            if (selected_role == 'Admin' and db_role not in ['Admin', 'Staff']) or \
               (selected_role == 'Guest' and db_role != 'Guest'):
                error = "Account does not have permission for the selected portal."
            else:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = db_role
                
                if db_role == 'Guest':
                    return redirect(url_for('guest.search'))
                else:
                    return redirect(url_for('dashboard.index'))
        else:
            error = "Invalid username or password."

    return render_template('auth/login.html', error=error)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            error = "Passwords do not match!"
        elif get_user_by_username(username):
            error = "Username already exists! Please choose another."
        else:
            # Hash the password to keep it secure
            hashed_pw = generate_password_hash(password)
            
            # BOOM: Actually saves to your database now!
            success = create_new_user(username, hashed_pw, 'Guest')
            
            if success:
                flash("Account created successfully! Please log in.")
                return redirect(url_for('auth.login'))
            else:
                error = "Database error: Could not create account."

    return render_template('auth/register.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))