from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User
from .import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Attempting login with email: {email}")
        print(f"Password: {password}")

        # Query the database for the user by email
        user = User.query.filter(User.email.ilike(email)).first()

        if user:  # Check if user exists
            if password == user.password:  # Check if passwords match
                if user.role_id == 'admin':  # Check if user is an admin
                    return render_template('dashboard.html')  # Render the dashboard for admins
                else:
                    flash('You do not have admin privileges.', 'danger')
                    # return redirect(url_for('auth.login'))  # Redirect back to login page
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('User not found with this email. Please check again.', 'danger')
            print(f"No user found with email: {email}")  # For debugging

    return render_template('login.html')
