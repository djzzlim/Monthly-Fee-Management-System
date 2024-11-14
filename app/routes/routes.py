from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from functools import wraps

def role_required(*roles):
    """Decorator to restrict access to users with specific role IDs."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if the current user is authenticated and has an allowed role ID
            if not current_user.is_authenticated or current_user.role_id not in roles:
                abort(403)  # Forbidden access if role does not match
            return f(*args, **kwargs)
        return decorated_function
    return decorator

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')  # Renders a home page

@main.route('/dashboard')
@login_required  # Ensure the user is logged in
def dashboard():
    return render_template('dashboard.html')