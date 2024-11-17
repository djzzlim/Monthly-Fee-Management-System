from flask import Blueprint, render_template, abort, current_app
from flask_login import login_required, current_user
from app.models.models import Settings
from functools import wraps

def app_name():
    app_name = "School Management System"
    with current_app.app_context():
        setting = Settings.query.filter_by(setting_key='school_name').first()
        if setting and setting.setting_value:
            app_name = setting.setting_value
    return app_name

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


routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html")


@routes.route('/dashboard')
@login_required  # Ensure the user is logged in
def dashboard():
    app_name = "School Management System"
    with current_app.app_context():
        setting = Settings.query.filter_by(setting_key='school_name').first()
        if setting and setting.setting_value:
            app_name = setting.setting_value
    return render_template('dashboard.html', app_name=app_name)

