from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db  # Importing db from the app package
from app.models.models import User, Role  # Import User and Role models from the models module

# Create the admin blueprint
admin = Blueprint('admin', __name__)

# Route to manage users
@admin.route('/manage_users')
@login_required
def manage_users():
    # Query the database to get all users
    users = User.query.all()  # Retrieve all users from the User table
    return render_template('admin/manage_users.html', users=users)

# Route to manage system settings (empty for now)
@admin.route('/system_settings')
@login_required
def system_settings():
    return render_template('admin/system_settings.html')

# Route to view reports (empty for now)
@admin.route('/reports')
@login_required
def reports():
    return render_template('admin/reports.html')

# Route to add a new user
@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form('username')
        email = request.form('email')
        password = request.form('password')  # Use the password directly without hashing
        role_id = request.form('role_id')

        # Check if the user already exists based on the email (optional, but good practice)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.add_user'))

        # Create a new user and save to the database
        new_user = User(username=username, email=email, password=password, role_id=role_id)
        db.session.add(new_user)
        db.session.commit()

        flash('New user added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    roles = Role.query.all()  # Fetch available roles
    return render_template('admin/add_user.html', roles=roles)

@admin.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Fetch user by ID (now a string)
    user = User.query.filter_by(id=user_id).first_or_404()  # Use filter_by to query by string ID
    
    if request.method == 'POST':
        # Handle form submission for editing user (updating user info)
        user.username = request.form['username']
        user.email = request.form['email']
        user.role_id = request.form['role_id']

        new_password = request.form['password']
        if new_password:
            user.password = new_password
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    roles = Role.query.all()  # Assuming you have a Role model for user roles
    return render_template('admin/edit_user.html', user=user, roles=roles)

@admin.route('/delete_user/<string:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Fetch the user by id
    user = User.query.filter_by(id=user_id).first_or_404()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))