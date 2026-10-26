from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app.models import User
from app.database import db

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            user = db.session.get(User, session['user_id'])
            if not user or user.role not in allowed_roles:
                flash(f'Access denied. Required role: {", ".join(allowed_roles)}.', 'danger')
                if user and user.role == 'cashier':
                    return redirect(url_for('billing.pos'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            if user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('billing.pos'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        if user:
            if user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            return redirect(url_for('billing.pos'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name or user.username
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                # Cashiers should only access billing
                if user.role == 'cashier' and not next_url.startswith('/billing'):
                    return redirect(url_for('billing.pos'))
                return redirect(next_url)

            if user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('billing.pos'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
