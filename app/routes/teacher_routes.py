from flask import Blueprint, render_template
from flask_login import login_required
from .routes import role_required  # Import your role_required decorator

teacher = Blueprint('teacher', __name__)

# Teacher Dashboard
@teacher.route('/')
@login_required
@role_required('2')  # Only users with role '2' (teacher) can access the dashboard
def dashboard():
    return render_template('teacher/dashboard.html')


# View Fee Status Route
@teacher.route('/fee-status')
@login_required
@role_required('2')
def fee_status():
    # Logic to retrieve and display fee status for students
    # Example: fee_status = get_fee_status_from_db()
    return render_template('teacher/fee_status.html')  # You would create this template


# Send Reminders to Parents Route
@teacher.route('/send-reminders')
@login_required
@role_required('2')
def send_reminders():
    # Logic to send reminders to parents about fees and assignments
    return render_template('teacher/send_reminders.html')  # You would create this template


# Generate Total Fee Route
@teacher.route('/generate-total-fee')
@login_required
@role_required('2')
def generate_total_fee():
    # Logic to calculate and display the total fee for all students
    # Example: total_fee = calculate_total_fee()
    return render_template('teacher/total_fee.html')  # You would create this template