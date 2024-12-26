from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app import db  # Importing db from the app package
# Import User and Role models from the models module
from app.models.models import User, Role, Settings, Class, ClassAssignment, ParentStudentRelation, FeeStructure
from .routes import role_required, app_name
from sqlalchemy import func
from datetime import datetime
from app.utilities.utils import allowed_file, compress_image, convert_to_favicon
import os
import uuid
import re

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

# Route to update the logo
@admin.route('/admin/update_logo', methods=['GET', 'POST'])
@login_required
@role_required('1')
def update_logo():
    print("Received request to update logo.")  # Debugging line

    if 'app_logo' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('system_settings'))

    file = request.files['app_logo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('system_settings'))

    if file and allowed_file(file.filename):
        filename = 'logo.png'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        try:
            print(f"Saving file to {filepath}")  # Debugging line
            file.save(filepath)

            # Compress the image after saving
            compress_image(filepath)

            # Optionally, create a favicon from the logo
            convert_to_favicon(filepath)

            flash('Logo updated successfully!', 'success')
        except Exception as e:
            print(f"Error saving file: {str(e)}")  # Debugging line
            flash(f'Error saving file: {str(e)}', 'danger')
    else:
        flash('Invalid file type or size!', 'danger')

    return redirect(url_for('admin.system_settings'))


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
                        if setting.setting_key == 'telegram_bot_api_key' and form_value.strip() == '':
                            # If the Telegram Bot API key is empty, set it to NULL
                            setting.setting_value = None
                        else:
                            setting.setting_value = form_value
                else:
                    # If form_value is None, this means the checkbox is unchecked, set it to '0' (or default value)
                    if setting.setting_key in ['email_notifications', 'sms_notifications']:
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


@admin.route('/update_fee_settings', methods=['GET', 'POST'])
@login_required
@role_required('1')
def update_fee_settings():
    if request.method == 'POST':
        try:
            # Retrieve specific fee settings keys
            late_fee_amount = request.form.get('late_fee_amount')
            due_date = request.form.get('due_date')
            discount_amount = request.form.get('discount_amount')

            # Validate and update each setting individually
            if late_fee_amount is not None:
                # Convert to float, round to 2 decimal places, and update in the database
                late_fee_setting = Settings.query.filter_by(setting_key='late_fee_amount').first()
                late_fee_setting.setting_value = str(round(float(late_fee_amount), 2))

            if due_date is not None:
                # Ensure the value is an integer
                due_date_setting = Settings.query.filter_by(setting_key='due_date').first()
                due_date_setting.setting_value = str(int(due_date))

            if discount_amount is not None:
                # Convert to float, round to 2 decimal places, and update in the database
                discount_setting = Settings.query.filter_by(setting_key='discount_amount').first()
                discount_setting.setting_value = str(round(float(discount_amount), 2))

            # Commit the changes to the database
            db.session.commit()

            # Flash success message and redirect
            flash('Fee settings updated successfully.', 'success')
            return redirect(url_for('admin.fee_management'))

        except Exception as e:
            # Flash error message in case of an exception
            flash(f'An error occurred while updating the fee settings: {str(e)}', 'danger')

    # For GET requests or error scenarios, render the settings page
    fee_settings = {
        'late_fee_amount': Settings.query.filter_by(setting_key='late_fee_amount').first(),
        'due_date': Settings.query.filter_by(setting_key='due_date').first(),
        'discount_amount': Settings.query.filter_by(setting_key='discount_amount').first()
    }
    return render_template('admin/fee_management.html', settings=fee_settings, app_name=app_name())


# Route to view class assignment (empty for now)
@admin.route('/class_assignments', methods=['GET', 'POST'])
@role_required('1')
@login_required
def class_assignments():
    # Fetch all users (teachers and students)
    teachers = User.query.filter_by(role_id='2').all()  # Assuming 'teacher' role_id
    students = User.query.filter_by(role_id='5').all()  # Assuming 'student' role_id
    classes = Class.query.all()  # All classes
    assignments = ClassAssignment.query.all()

    if request.method == 'POST':
        # Handle deletion of selected assignments
        if 'delete_selected' in request.form:
            assignment_ids = request.form.getlist('assignment_ids')
            if assignment_ids:
                ClassAssignment.query.filter(ClassAssignment.assignment_id.in_(assignment_ids)).delete(synchronize_session=False)
                db.session.commit()
                flash("Selected assignments have been deleted.", "success")
                return redirect(url_for('admin.class_assignments'))

        # Handle class assignment creation (POST request for form submission)
        class_id = request.form.get('class_id')
        teacher_id = request.form.get('teacher_id')
        student_ids = request.form.getlist('student_id')  # Allow selecting multiple students
        
        # Validate input
        if not class_id or not teacher_id or not student_ids:
            flash("All fields are required!", "danger")
            return redirect(url_for('admin.class_assignments'))

        # Track duplicates
        skipped_students = []

        # Create ClassAssignment records for each student, checking for duplicates
        for student_id in student_ids:
            # Check if the student is already assigned to any class
            existing_student_assignment = ClassAssignment.query.filter_by(student_id=student_id).first()
            if existing_student_assignment:
                # If student already assigned to a class, add to skipped list
                skipped_students.append(f"Student {student_id} is already assigned to a class.")
            else:
                # If no duplicate, create new assignment
                new_assignment = ClassAssignment(
                    class_id=class_id,
                    teacher_id=teacher_id,
                    student_id=student_id
                )
                db.session.add(new_assignment)

        # Commit the new assignments to the database
        db.session.commit()

        if skipped_students:
            flash(f"Some assignments were skipped due to existing assignments: {', '.join(skipped_students)}", "warning")
        else:
            flash("Class Assignment(s) successfully created!", "success")
        
        return redirect(url_for('admin.class_assignments'))
    
    return render_template(
        'admin/class_assignments.html',
        teachers=teachers,
        students=students,
        classes=classes,
        assignments=assignments,
        app_name=app_name()
    )



# Route to view parent student (empty for now)
@admin.route('/parent_student', methods=['GET', 'POST'])
@login_required
@role_required('1')  # Only accessible by Admin
def parent_student():
    # Fetch all students and parents
    parents = User.query.filter_by(role_id=3).all()  # Parents have role_id = 3
    students = User.query.filter_by(role_id=5).all()  # Students have role_id = 5

    # Create a dictionary of student_id to parent_id from ParentStudentRelation
    parent_student_map = {
        relation.student_id: relation.parent_id
        for relation in ParentStudentRelation.query.all()
    }

    if request.method == 'POST':
        # Loop through students and assign the selected parent
        for student in students:
            parent_id = request.form.get(f'parent_id_{student.id}')
            if parent_id:
                # Check if the student already has a parent
                existing_relation = ParentStudentRelation.query.filter_by(student_id=student.id).first()
                if existing_relation:
                    # Update the existing relation
                    existing_relation.parent_id = parent_id
                else:
                    # Create a new relationship
                    new_relation = ParentStudentRelation(parent_id=parent_id, student_id=student.id)
                    db.session.add(new_relation)
                db.session.commit()

        flash("Parent-Student relationships updated successfully!", "success")
        return redirect(url_for('admin.parent_student'))

    # Pass the parent-student mapping to the template
    return render_template(
        'admin/parent_student.html',
        students=students,
        parents=parents,
        parent_student_map=parent_student_map,  # Provide the map for pre-selection
        app_name=app_name()
    )


# Route to view fee management (empty for now)
@admin.route('/fee_management')
@login_required
@role_required('1')
def fee_management():
    # Fetch all fee structures from the database
    fee_structures = FeeStructure.query.all()

    # Fetch specific settings related to fees
    fee_settings = {
        'late_fee_amount': Settings.query.filter_by(setting_key='late_fee_amount').first(),
        'due_date': Settings.query.filter_by(setting_key='due_date').first(),
        'discount_amount': Settings.query.filter_by(setting_key='discount_amount').first()
    }

    # Convert settings to a dictionary for easier access in the template
    settings = {
        key: setting.setting_value if setting else None
        for key, setting in fee_settings.items()
    }

    return render_template(
        'admin/fee_management.html',
        fee_structures=fee_structures,
        settings=settings,
        app_name=app_name()
    )

@admin.route('/add_fee_structure', methods=['GET', 'POST'])
@login_required
@role_required('1')
def add_fee_structure():
    if request.method == 'POST':
        # Handle form submission (creating a new fee structure)
        description = request.form['description']
        total_fee = request.form['total_fee']
        new_fee_structure = FeeStructure(description=description, total_fee=total_fee)
        db.session.add(new_fee_structure)
        db.session.commit()
        flash('Fee Structure Added Successfully!', 'success')
        return redirect(url_for('admin.fee_management'))
    return render_template('admin/add_fee_structure.html', app_name=app_name())

@admin.route('/edit_fee_structure/<id>', methods=['GET', 'POST'])
@login_required
@role_required('1')
def edit_fee_structure(id):
    fee_structure = FeeStructure.query.get(id)
    
    if not fee_structure:
        flash('Fee Structure not found!', 'danger')
        return redirect(url_for('admin.fee_management'))
    
    # Handle the form submission
    if request.method == 'POST':
        fee_structure.description = request.form['description']
        fee_structure.total_fee = request.form['total_fee']
        fee_structure.other_field = request.form.get('other_field', '')  # Optional field, handle with .get()

        db.session.commit()
        flash('Fee Structure updated successfully!', 'success')
        return redirect(url_for('admin.fee_management'))

    return render_template('admin/edit_fee_structure.html', fee_structure=fee_structure, app_name=app_name())

@admin.route('/update_fee_structure/<id>', methods=['POST'])
@login_required
@role_required('1')
def update_fee_structure(id):
    # Retrieve the FeeStructure object from the database
    fee_structure = FeeStructure.query.get(id)

    if fee_structure:
        # Update the fields with the new values from the form
        fee_structure.description = request.form['description']
        fee_structure.total_fee = request.form['total_fee']

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash('Fee Structure Updated Successfully!', 'success')
    else:
        flash('Fee Structure not found.', 'danger')

    # Redirect to the fee management page after updating
    return redirect(url_for('admin.fee_management'))

# Fee Structure: Delete
@admin.route('/delete_fee_structure/<id>')
@login_required
@role_required('1')
def delete_fee_structure(id):
    fee_structure = FeeStructure.query.get(id)
    db.session.delete(fee_structure)
    db.session.commit()
    flash('Fee Structure Deleted Successfully!', 'success')
    return redirect(url_for('admin.fee_management'))

# Route to add a new user
@admin.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required('1')
def add_user():
    roles = Role.query.all()
    password_policy_setting = Settings.query.filter_by(setting_key='password_policy').first()
    password_policy = password_policy_setting.setting_value if password_policy_setting else 'simple'  # Default to 'simple' if not set

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role')
        date_of_birth_str = request.form.get('date_of_birth')  # Fetch date of birth as string

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.add_user'))

        # Convert date_of_birth from string to date
        date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date() if date_of_birth_str else None

        # Password validation (backend)
        if password_policy == 'strong':
            strong_password_regex = r'^(?=.*[0-9])(?=.*[\W_]).{8,}$'
            if not re.match(strong_password_regex, password):
                flash('Password must be at least 8 characters long and contain at least one number and one special character.', 'danger')
                return redirect(url_for('admin.add_user'))
        else:
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('admin.add_user'))

        # Generate user ID and create a new user
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

        # Add and commit the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/add_user.html', roles=roles, password_policy=password_policy, app_name=app_name())


@admin.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('1')
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    roles = Role.query.all()
    password_policy_setting = Settings.query.filter_by(setting_key='password_policy').first()
    password_policy = password_policy_setting.setting_value if password_policy_setting else 'simple'  # Default to 'simple' if not set

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

        if new_password:
            if password_policy == 'strong':
                strong_password_regex = r'^(?=.*[0-9])(?=.*[\W_]).{8,}$'
                if not re.match(strong_password_regex, new_password):
                    flash('Password must be at least 8 characters long, contain at least one number and one special character.', 'danger')
                    return redirect(url_for('admin.edit_user', user_id=user.id))
            else:  # Simple policy
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters long.', 'danger')
                    return redirect(url_for('admin.edit_user', user_id=user.id))

            user.password = new_password  # Update the password if valid

        if user.role_id == '4':
            user.password = None

        existing_user = User.query.filter_by(email=user.email).first()
        if existing_user and existing_user.id != user.id:
            flash('User with this email already exists!', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        db.session.commit()
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=user, roles=roles, password_policy=password_policy, app_name=app_name())


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
