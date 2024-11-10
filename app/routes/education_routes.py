from flask import Blueprint, render_template
from flask_login import login_required

# Create the education (teacher) blueprint
education = Blueprint('education', __name__)

@education.route('/student_fees')
@login_required
def student_fees():
    return render_template('education/student_fees.html')

@education.route('/send_reminders')
@login_required
def send_reminders():
    return render_template('education/send_reminders.html')
