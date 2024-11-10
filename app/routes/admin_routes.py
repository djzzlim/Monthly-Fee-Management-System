from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Create the admin blueprint
admin = Blueprint('admin', __name__)

@admin.route('/manage_users')
@login_required
def manage_users():
    # Admin route to manage users
    return render_template('admin/manage_users.html')

@admin.route('/system_settings')
@login_required
def system_settings():
    # Admin route to configure system settings
    return render_template('admin/system_settings.html')

@admin.route('/reports')
@login_required
def reports():
    # Admin route to view reports
    return render_template('admin/reports.html')
