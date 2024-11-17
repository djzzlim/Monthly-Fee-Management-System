import re
import smtplib

from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

from app.models.models import User

auth = Blueprint('auth', __name__)

# Email regex pattern for basic validation
email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate email format using regex
        if not re.match(email_regex, email):
            flash('Invalid email format. Please check the email address.', 'danger')
            return render_template('auth/login.html')

        # Query the database for the user by email
        user = User.query.filter_by(email=email).first()

        if user:  # Check if user exists
            if user.role_id == '5':
                flash('Students are not allowed to log in.', 'danger')
                return render_template('login.html')

            if password == user.password:  # Check if passwords match
                login_user(user)  # Log in the user

                # Redirect to the dashboard based on the role
                if current_user.role_id == '1':  # Admin
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role_id == '4':  # Accountant
                    return redirect(url_for('accountant.dashboard'))
                else:
                    return redirect(url_for('routes.home'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('User not found with this email. Please check again.', 'danger')

    return render_template('auth/login.html')


# Route for logging out
@auth.route('/logout')
def logout():
    logout_user()  # Log out the current user
    # Redirect to home page or login page
    return redirect(url_for('routes.home'))


@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Get the email from the form
        email = request.form.get('email')

        # Validate the email format using regex
        if not re.match(email_regex, email):
            flash('Invalid email format. Please check the email address.', 'danger')
            return render_template('forgot-password.html')

        # Here, you would normally send a reset link to the email.
        # For now, let's just flash a success message and redirect.
        flash('Password reset link has been sent to your email.', 'success')
        # Assuming '/login' is your login page route
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')
