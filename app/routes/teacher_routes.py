from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
import datetime
import pytz
from app import db
from app.models.models import User, FeeRecord, StudentFeeAssignment, PaymentStatus, ClassAssignment, Class
from app.models.models import Notification, MessageTemplate, ParentStudentRelation
from app.models.models import FeeStructure
from flask import jsonify
import uuid
from .routes import role_required, app_name

teacher = Blueprint('teacher', __name__)

# Teacher Dashboard
@teacher.route('/')
@login_required
@role_required('2')
def dashboard():
    return render_template('teacher/dashboard.html', app_name=app_name())

# View Fee Status Route
@teacher.route('/fee-status')
@login_required
@role_required('2')
def fee_status():
    # Get the class name from the query parameters (if it exists)
    selected_class = request.args.get('class_name', None)
    
    # Fetch student fee records with related information
    query = (
        db.session.query(
            User.first_name, 
            User.last_name, 
            Class.class_name, 
            FeeRecord.amount_due, 
            FeeRecord.total_amount, 
            PaymentStatus.status_name,
            FeeRecord.date_assigned  # Use date_assigned here
        )
        .join(ClassAssignment, ClassAssignment.student_id == User.id)  # Join to filter by teacher's classes
        .join(Class, Class.class_id == ClassAssignment.class_id)
        .join(StudentFeeAssignment, StudentFeeAssignment.student_id == User.id)
        .join(FeeRecord, FeeRecord.fee_assignment_id == StudentFeeAssignment.fee_assignment_id)
        .join(PaymentStatus, PaymentStatus.status_id == FeeRecord.status_id)
        .filter(ClassAssignment.class_id.in_(
            db.session.query(ClassAssignment.class_id)
            .filter(ClassAssignment.teacher_id == current_user.id)  # Only classes assigned to the teacher
        ))
    )
    
    # If class_name is provided, filter the records by class
    if selected_class:
        query = query.filter(Class.class_name == selected_class)

    fee_data = query.all()

    # Format data for template, include date_assigned
    payments = [{
        "student_name": f"{record.first_name} {record.last_name}",
        "class_name": record.class_name,
        "amount_due": record.amount_due,
        "paid_amount": record.total_amount,
        "payment_status": record.status_name,
        "date_assigned": record.date_assigned.strftime('%Y-%m-%d')  # Format the date as required
    } for record in fee_data]

    # Calculate the total number of students and percentage for each status
    total_students = len(fee_data)
    paid_count = sum(1 for record in fee_data if record.status_name == 'Paid')
    pending_count = sum(1 for record in fee_data if record.status_name == 'Pending')
    overdue_count = sum(1 for record in fee_data if record.status_name == 'Overdue')

    paid_percentage = (paid_count / total_students * 100) if total_students else 0
    pending_percentage = (pending_count / total_students * 100) if total_students else 0
    overdue_percentage = (overdue_count / total_students * 100) if total_students else 0

    # Fetch available class names for the dropdown, ensuring no duplicates and filtering by teacher's assignments
    class_names = (
        db.session.query(Class.class_name)
        .join(ClassAssignment)
        .filter(ClassAssignment.teacher_id == current_user.id)
        .distinct()
        .all()
    )
    class_names = [class_name[0] for class_name in class_names]  # Extract class names

    return render_template(
        'teacher/fee_status.html', 
        payments=payments, 
        class_names=class_names, 
        selected_class=selected_class,
        total_students=total_students,
        paid_percentage=paid_percentage,
        pending_percentage=pending_percentage,
        overdue_percentage=overdue_percentage, 
        app_name=app_name()
    )


# Fetch students based on class or all assigned to teacher
@teacher.route('/get_students', methods=['POST'])
@login_required
@role_required('2')  # Ensure the user has the teacher role
def get_students():
    data = request.get_json()
    class_name = data.get("class_name")

    # Subquery to get class IDs assigned to the current teacher
    teacher_classes = (
        db.session.query(ClassAssignment.class_id)
        .filter(ClassAssignment.teacher_id == current_user.id)
        .scalar_subquery()
    )

    # Query to get students assigned to the teacher's classes
    query = (
        db.session.query(User.id, User.first_name, User.last_name)
        .join(ClassAssignment, ClassAssignment.student_id == User.id)
        .filter(ClassAssignment.class_id.in_(teacher_classes))
    )

    # Filter by class name if provided and not "all"
    if class_name and class_name != "all":
        query = query.join(Class, Class.class_id == ClassAssignment.class_id).filter(Class.class_name == class_name)

    students = query.all()
    if not students:
        return jsonify({"students": []})

    return jsonify({
        "students": [{"id": student.id, "name": f"{student.first_name} {student.last_name}"} for student in students]
    })


@teacher.route('/send-reminders', methods=['GET', 'POST'])
@login_required
@role_required('2')
def send_reminders():
    if request.method == 'POST':
        message_template_id = request.form.get('messageTemplate')  
        search_student = request.form.get('searchStudent')
        selected_class = request.form.get('class_name')
        custom_message = request.form.get('Message')  
        message_type = request.form.get('messageType')

        template = None
        if message_template_id:
            template = db.session.query(MessageTemplate).filter_by(message_temp_id=message_template_id).first()

        original_message_text = template.template_text if template else custom_message

        students_query = (
            db.session.query(User)
            .join(ClassAssignment, ClassAssignment.student_id == User.id)
            .filter(ClassAssignment.class_id.in_(
                db.session.query(ClassAssignment.class_id)
                .filter(ClassAssignment.teacher_id == current_user.id)
            ))
        )

        if selected_class and selected_class != "all":
            students_query = students_query.filter(Class.class_name == selected_class)

        if search_student and search_student != "all":
            students_query = students_query.filter(User.id == search_student)

        students = students_query.all()

        if not students:
            flash('No students found or selected!', 'danger')
            return redirect(url_for('teacher.send_reminders'))

        last_notification = db.session.query(Notification).order_by(Notification.notification_id.desc()).first()
        last_number = int(last_notification.notification_id.replace('notif', '')) if last_notification else 0  

        batch_size = 5
        notifications = []
        skipped_students = 0  # Counter for students skipped due to missing statuses

        for index, student in enumerate(students, 1):
            last_number += 1  
            notification_id = f'notif{last_number}'  

            while db.session.query(Notification).filter_by(notification_id=notification_id).first():
                last_number += 1
                notification_id = f'notif{last_number}'  

            message_text = original_message_text  

            if message_template_id:  
                fee_record = (
                    db.session.query(FeeRecord)
                    .join(StudentFeeAssignment, StudentFeeAssignment.fee_assignment_id == FeeRecord.fee_assignment_id)
                    .join(PaymentStatus, PaymentStatus.status_id == FeeRecord.status_id)
                    .filter(StudentFeeAssignment.student_id == student.id)
                    .order_by(FeeRecord.due_date.desc())
                    .first()
                )

                if not fee_record:
                    skipped_students += 1
                    continue  

                fee_status = fee_record.status.status_id  

                # ✅ Ensure correct template is used for the respective fee status
                if fee_status == 'status001':  # Unpaid Fees
                    if template.message_temp_id != 'template1':  
                        skipped_students += 1
                        continue  # Skip if wrong template is selected
                    message_text = template.template_text.replace('{amount}', str(fee_record.total_amount))
                    message_text = message_text.replace('{date}', str(fee_record.due_date.strftime('%Y-%m-%d')))
                
                elif fee_status == 'status003':  # Overdue Fees
                    if template.message_temp_id != 'template2':  
                        skipped_students += 1
                        continue  # Skip if wrong template is selected
                    message_text = template.template_text.replace('{amount}', str(fee_record.total_amount))
                    message_text = message_text.replace('{date}', str(fee_record.due_date.strftime('%Y-%m-%d')))
                else:
                    skipped_students += 1
                    continue  # Skip if the status is not relevant

            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            malaysia_time = datetime.datetime.now(malaysia_tz)

            notification = Notification(
                notification_id=notification_id,
                teacher_id=current_user.id,
                student_id=student.id,
                message_type=message_type,
                message_text=message_text,
                timestamp=malaysia_time
            )

            notifications.append(notification)
            db.session.add(notification)

            if index % batch_size == 0:
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error sending reminders: {e}', 'danger')
                    return redirect(url_for('teacher.send_reminders'))

        try:
            db.session.commit()
            if skipped_students > 0:
                if search_student and search_student != "all" and len(students) == 1:
                    student = students[0]  # Get the single student object
                    flash(f'Student "{student.first_name} {student.last_name}" does not have the required fee status or template mismatch.', 'warning')
                else:
                    flash(f'Some students were skipped due to missing fee statuses or template mismatches.', 'warning')
            else:
                flash('Reminders sent successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error sending reminders: {e}', 'danger')

        return redirect(url_for('teacher.send_reminders'))

    class_names = db.session.query(Class.class_name).join(ClassAssignment).filter(
        ClassAssignment.teacher_id == current_user.id
    ).distinct().all()
    class_names = [class_name[0] for class_name in class_names]

    templates = db.session.query(MessageTemplate).filter(MessageTemplate.message_temp_id != 'template3').all()

    return render_template('teacher/send_reminders.html', class_names=class_names, templates=templates, app_name=app_name())
   

@teacher.route('/generate-total-fee')
@login_required
@role_required('2')
def generate_total_fee():
    selected_class = request.args.get('class_name', None)

    # Query to fetch fee details for students
    query = (
        db.session.query(
            User.first_name,
            User.last_name,
            Class.class_name,
            FeeRecord.total_amount,
            FeeRecord.status_id,
            PaymentStatus.status_name
        )
        .join(ClassAssignment, ClassAssignment.student_id == User.id)
        .join(Class, Class.class_id == ClassAssignment.class_id)
        .join(StudentFeeAssignment, StudentFeeAssignment.student_id == User.id)
        .join(FeeRecord, FeeRecord.fee_assignment_id == StudentFeeAssignment.fee_assignment_id)
        .join(PaymentStatus, PaymentStatus.status_id == FeeRecord.status_id)
        .filter(ClassAssignment.class_id.in_(
            db.session.query(ClassAssignment.class_id)
            .filter(ClassAssignment.teacher_id == current_user.id)
        ))
    )

    # Filter by selected class if provided
    if selected_class:
        query = query.filter(Class.class_name == selected_class)

    # Fetch all matching records
    fee_records = query.all()

    # Compute total collected amount and total fee recorded based on class selection
    filtered_fee_records = fee_records if not selected_class else [record for record in fee_records if record.class_name == selected_class]

    total_collected_fee = sum(record.total_amount for record in filtered_fee_records if record.status_name == 'Paid')
    total_fee_recorded = sum(record.total_amount for record in filtered_fee_records)

    # Prepare student fee data
    students = {}
    for record in filtered_fee_records:
        student_name = f"{record.first_name} {record.last_name}"
        if student_name not in students:
            students[student_name] = {
                "class_name": record.class_name,
                "total_fee": 0.0,
                "collected_fee": 0.0
            }

        students[student_name]["total_fee"] += float(record.total_amount) if record.total_amount else 0.0
        if record.status_name == "Paid":
            students[student_name]["collected_fee"] += float(record.total_amount)

    # Convert dictionary to list
    student_list = [{"name": name, **data} for name, data in students.items()]

    # Fetch available class names for dropdown
    class_names = (
        db.session.query(Class.class_name)
        .join(ClassAssignment, ClassAssignment.class_id == Class.class_id)
        .filter(ClassAssignment.teacher_id == current_user.id)
        .distinct()
        .all()
    )
    class_names = [class_name[0] for class_name in class_names]

    # Set the title dynamically based on selection
    fee_summary_title = f"Total Fee for Class {selected_class}" if selected_class else "Total Fee for All Classes"

    return render_template(
        'teacher/total_fee.html',
        students=student_list,
        total_collected_fee=total_collected_fee,
        total_fee_recorded=total_fee_recorded,
        class_names=class_names,
        selected_class=selected_class,
        fee_summary_title=fee_summary_title,
        app_name=app_name()
    )

