import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from .models import User

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
            return render_template('login.html')

        # Query the database for the user by email
        user = User.query.filter_by(email=email).first()

        if user:  # Check if user exists
            if password == user.password:  # Check if passwords match
                login_user(user)  # Log in the user

                # Redirect to the dashboard based on the role
                return redirect(url_for('main.dashboard'))  # Redirect to dashboard route
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('User not found with this email. Please check again.', 'danger')

    return render_template('login.html')

# Route for logging out
@auth.route('/logout')
def logout():
    logout_user()  # Log out the current user
    return redirect(url_for('main.home'))  # Redirect to home page or login page

@auth.route('/forgot-password')
def forgot_password():
    return redirect(url_for('main.home'))