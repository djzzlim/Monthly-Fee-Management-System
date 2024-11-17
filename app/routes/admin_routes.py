from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db  # Importing db from the app package
# Import User and Role models from the models module
from app.models.models import User, Role, Settings
from .routes import role_required, app_name
from sqlalchemy import func
from datetime import datetime
import uuid

# Create the admin blueprint
admin = Blueprint('admin', __name__)

# Route for the admin dashboard


@admin.route('/')
@login_required
@role_required('1')
def dashboard():
    return render_template('admin/admin.html', app_name=app_name())


# Route to manage users
@admin.route('/manage_users')
@login_required
@role_required('1')
def manage_users():
    # Query the database to get all users
    users = User.query.all()  # Retrieve all users from the User table
    return render_template('admin/manage_users.html', users=users, app_name=app_name())


@admin.route('/system-settings', methods=['GET', 'POST'])
@login_required
@role_required('1')
def system_settings():
    # Retrieve all settings from the database
    settings = {
        setting.setting_key: setting.setting_value for setting in Settings.query.all()}

    # Pass settings to the template
    return render_template('admin/system_settings.html', settings=settings, app_name=app_name())

# Route to manage system settings (empty for now)


@admin.route('/update_settings', methods=['GET', 'POST'])
@login_required
@role_required('1')
def update_settings():
    if request.method == 'POST':
        try:
            # Retrieve all settings from the database
            settings = Settings.query.all()

            # Loop through settings and update their values based on form input
            for setting in settings:
                form_value = request.form.get(setting.setting_key)

                # Handle checkbox logic separately (checkboxes may or may not be included in the form submission)
                if form_value is not None:
                    if form_value == 'on':  # Checkbox is checked, set to '1'
                        setting.setting_value = '1'
                    else:
                        # Special handling for specific settings
                        if setting.setting_key == 'late_fee_amount':
                            # Convert to float, round to 2 decimal places, and convert back to string
                            setting.setting_value = str(
                                round(float(form_value), 2))
                        elif setting.setting_key == 'telegram_bot_api_key' and form_value.strip() == '':
                            # If the Telegram Bot API key is empty, set it to NULL
                            setting.setting_value = None
                        else:
                            setting.setting_value = form_value
                else:
                    # If form_value is None, this means the checkbox is unchecked, set it to '0' (or default value)
                    if setting.setting_key in ['email_notifications', 'sms_notifications', 'two_factor_auth']:
                        setting.setting_value = '0'  # Unchecked checkboxes default to '0'

            # Commit the changes to the database
            db.session.commit()

            # Redirect to the dashboard
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            # If there's any error, flash an error message
            flash(
                f'An error occurred while updating the settings: {str(e)}', 'danger')

    # If it's a GET request, or in case of an error, stay on the settings page
    return render_template('admin/system_settings.html', settings=Settings.query.all(), app_name=app_name())


# Route to view reports (empty for now)
@admin.route('/reports')
@role_required('1')
@login_required
def reports():
    return render_template('admin/reports.html', app_name=app_name())

# Route to add a new user


@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required('1')
def add_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role')
        date_of_birth_str = request.form.get(
            'date_of_birth')  # Fetch date of birth as string

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists!', 'danger')
            # return render_template('admin/add_user.html', app_name=app_name())
            return render_template('admin/add_user.html', roles=roles, app_name=app_name())

        # Convert date_of_birth from string to date
        date_of_birth = datetime.strptime(
            date_of_birth_str, '%Y-%m-%d').date() if date_of_birth_str else None

        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role_id=role_id,
            date_of_birth=date_of_birth  # Pass the date object to the database
        )

        db.session.add(new_user)
        db.session.commit()

        return render_template('admin/manage_user.html', roles=roles, app_name=app_name())

    roles = Role.query.all()
    return render_template('admin/add_user.html', roles=roles, app_name=app_name())


@admin.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('1')
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    roles = Role.query.all()

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.role_id = request.form['role_id']

        # Convert date_of_birth from string to date
        date_of_birth_str = request.form['date_of_birth']
        user.date_of_birth = datetime.strptime(
            date_of_birth_str, '%Y-%m-%d').date()

        new_password = request.form['password']

        if user.role_id == '4':
            user.password = None
        elif new_password:
            user.password = new_password

        existing_user = User.query.filter_by(email=user.email).first()
        if existing_user and existing_user.id != user.id:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        db.session.commit()
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=user, roles=roles, app_name=app_name())


@admin.route('/delete_user/<string:user_id>', methods=['POST'])
@login_required
@role_required('1')
def delete_user(user_id):
    # Fetch the user by id
    user = User.query.filter_by(id=user_id).first_or_404()

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin.manage_users'))
