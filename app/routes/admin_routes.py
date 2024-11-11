from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db  # Importing db from the app package
from app.models.models import User, Role  # Import User and Role models from the models module
from sqlalchemy import func
import uuid

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
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        password = request.form.get('password')  # Ensure to hash the password in production
        role_id = request.form.get('role')

        # Check if the user already exists based on the email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.add_user'))

        # Generate a new UUID for the user ID
        user_id = str(uuid.uuid4())

        # Create a new user with the generated UUID
        new_user = User(id=user_id, first_name=first_name, last_name=last_name, email=email, password=password, role_id=role_id)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('admin.manage_users'))

    roles = Role.query.all()  # Fetch available roles
    return render_template('admin/add_user.html', roles=roles)

@admin.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Fetch user by ID (now a string)
    user = User.query.filter_by(id=user_id).first_or_404()  # Use filter_by to query by string ID
    
    # Fetch roles for the dropdown menu
    roles = Role.query.all()

    if request.method == 'POST':
        # Handle form submission for editing user (updating user info)
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.role_id = request.form['role_id']

        new_password = request.form['password']
        
        # Check if the role is "student" (adjust this if your student role has a different ID)
        if user.role_id == '4':
            user.password = None
        elif new_password:
            user.password = new_password

        # Check if the email already exists for another user
        existing_user = User.query.filter_by(email=user.email).first()
        if existing_user and existing_user.id != user.id:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id, roles=roles))
        
        # Commit changes to the database
        db.session.commit()
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=user, roles=roles)


@admin.route('/delete_user/<string:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Fetch the user by id
    user = User.query.filter_by(id=user_id).first_or_404()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin.manage_users'))