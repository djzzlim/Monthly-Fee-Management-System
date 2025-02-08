from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.models import Class, ClassAssignment, User
from . import admin
from app.routes.routes import role_required, app_name

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