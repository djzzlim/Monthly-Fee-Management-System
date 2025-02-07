import random
from flask import Blueprint, flash, jsonify, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from .routes import role_required
from ..models.models import User, ParentStudentRelation, StudentFeeAssignment, FeeStructure, FeeRecord, Settings, PaymentHistory, Notification  # Adjust import paths as needed
import datetime
import logging
import os
from fpdf import FPDF
from flask import send_from_directory
from .. import db

parent = Blueprint('parent', __name__)

@parent.route('/')
@login_required
@role_required('3')  # Ensure the user has the parent role
def dashboard():
    try:
        # Fetch children related to the current parent
        children = (
            db.session.query(User)
            .join(ParentStudentRelation, ParentStudentRelation.student_id == User.id)
            .filter(ParentStudentRelation.parent_id == current_user.id)
            .all()
        )

        # If no children are associated, display an error message
        if not children:
            return render_template(
                'error.html',
                error_message="No children are associated with this parent account."
            )

        # Retrieve selected child ID from the session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            # Randomly select a child if no child is selected
            random_child = random.choice(children)
            session[user_specific_key] = random_child.id
            selected_child = random_child
        else:
            # Fetch the selected child's details
            selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        return render_template('parent/parent.html', children=children, selected_child=selected_child)
    except Exception as e:
        return render_template('error.html', error_message=str(e))


@parent.route('/select_child', methods=['POST'])
@login_required
@role_required('3')
def select_child():
    try:
        # Retrieve child ID from form submission
        child_id = request.form.get('child_id')

        # Validate if the child belongs to the parent
        is_child_valid = (
            db.session.query(ParentStudentRelation)
            .filter_by(parent_id=current_user.id, student_id=child_id)
            .first()
        )

        if is_child_valid:
            # Store selected child ID in session
            user_specific_key = f'selected_child_id_{current_user.id}'
            session[user_specific_key] = child_id  # Store in session with a user-specific key
        else:
            # Clear session if validation fails
            user_specific_key = f'selected_child_id_{current_user.id}'
            session.pop(user_specific_key, None)

        return redirect(url_for('parent.dashboard'))
    except Exception as e:
        return render_template('error.html', error_message=str(e))

@parent.route('/fee_summary')
@login_required
@role_required('3')
def fee_summary():
    try:
        # Get the selected child from the session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        # Fetch the selected child's details
        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        # Fetch fee assignments related to the selected child
        fee_assignments = db.session.query(StudentFeeAssignment).filter_by(student_id=selected_child_id).all()

        # Fetch fee records for all the fee assignments
        fee_records = []
        for assignment in fee_assignments:
            records = db.session.query(FeeRecord).filter_by(fee_assignment_id=assignment.fee_assignment_id).all()
            fee_records.extend(records)

        # Initialize totals
        total_amount_due = sum(record.amount_due for record in fee_records if record.status_id != "status002")  # Exclude paid fees
        total_penalty = sum(record.late_fee_amount for record in fee_records if record.status_id != "status002")
        total_amount_with_penalty = total_amount_due + total_penalty

        # Ensure current_date is passed to the template
        current_date = datetime.datetime.now().date()

        return render_template(
            'parent/fee_summary.html',
            selected_child=selected_child,
            fee_records=fee_records,
            total_amount_due=total_amount_due,
            total_penalty=total_penalty,
            total_amount_with_penalty=total_amount_with_penalty,
            current_date=current_date  # Pass current_date here
        )
    except Exception as e:
        return render_template('error.html', error_message=str(e))


@parent.route('/fee_record')
@login_required
@role_required('3')
def fee_record():
    try:
        # Get the selected child from the session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        # Fetch the selected child
        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        # Fetch fee assignments
        fee_assignments = db.session.query(StudentFeeAssignment).filter_by(student_id=selected_child_id).all()

        # Fetch fee records and associated details
        fee_records = []
        for assignment in fee_assignments:
            records = db.session.query(FeeRecord).filter_by(fee_assignment_id=assignment.fee_assignment_id).all()
            fee_records.extend(records)

        # Initialize totals
        total_amount_due = sum(record.amount_due for record in fee_records if record.status_id != "status002")
        total_penalty = sum(record.late_fee_amount for record in fee_records if record.status_id != "status002")
        total_amount_with_penalty = total_amount_due + total_penalty

        return render_template(
            'parent/fee_record.html',
            selected_child=selected_child,
            fee_records=fee_records,
            total_amount_due=total_amount_due,
            total_penalty=total_penalty,
            total_amount_with_penalty=total_amount_with_penalty
        )
    except Exception as e:
        return render_template('error.html', error_message=str(e))

@parent.route('/download_invoice/<fee_record_id>')
@login_required
@role_required('3')
def download_invoice(fee_record_id):
    try:
        # Define the invoice directory
        invoice_dir = os.path.join(os.getcwd(), 'app', 'archives', 'invoices')

        # Construct the expected invoice filename
        invoice_filename = f'invoice_{fee_record_id}.pdf'
        invoice_path = os.path.join(invoice_dir, invoice_filename)

        # Check if the file exists
        if not os.path.exists(invoice_path):
            return render_template('error.html', error_message="Invoice not found.")

        # Send the file for download
        return send_from_directory(invoice_dir, invoice_filename, as_attachment=False)

    except Exception as e:
        return render_template('error.html', error_message=str(e))



@parent.route('/make_payment', methods=['GET', 'POST'])
@login_required
@role_required('3')
def make_payment():
    try:
        # Get the selected child from the session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        # Fetch the selected child
        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()
        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        # Fetch unpaid fee records for the selected child (excluding status '002')
        unpaid_fees = (
            db.session.query(FeeRecord)
            .join(StudentFeeAssignment)
            .filter(
                StudentFeeAssignment.student_id == selected_child.id,
                FeeRecord.status_id.in_(['status001', 'status003'])  # Only show unpaid or pending fees
            )
            .all()
        )

        no_payment_due = len(unpaid_fees) == 0  # True if no fees available for payment
        total_penalty = 0
        fee_record = None

        if not no_payment_due:
            fee_record = unpaid_fees[0]  # Default to first unpaid fee
            total_penalty = fee_record.late_fee_amount if fee_record else 0

        if request.method == 'POST':
            fee_payment_id = request.form.get('fee_payment')
            payment_method = request.form.get('payment_method')

            selected_fee_record = db.session.query(FeeRecord).filter_by(fee_record_id=fee_payment_id).first()
            if not selected_fee_record:
                flash('Invalid fee selection.', 'danger')
                return redirect(url_for('parent.make_payment'))

            if not payment_method:
                flash('Please select a payment method.', 'danger')
                return redirect(url_for('parent.make_payment'))

            # Generate PaymentHistoryId in 'ph<new number>' format
            last_payment = db.session.query(PaymentHistory).order_by(PaymentHistory.history_id.desc()).first()
            new_number = int(last_payment.history_id[2:]) + 1 if last_payment else 1
            new_payment_id = f'ph{new_number}'

            new_payment = PaymentHistory(
                history_id=new_payment_id,
                fee_record_id=selected_fee_record.fee_record_id,
                amount_paid=selected_fee_record.total_amount,
                payment_method=payment_method,
                payment_date=datetime.datetime.utcnow()
            )

            # Update fee record status to 'PAID' (status002)
            selected_fee_record.status_id = 'status002'
            selected_fee_record.last_updated_date = datetime.datetime.utcnow()

            db.session.add(new_payment)
            db.session.commit()

            # Generate PDF Receipt
            generate_receipt_pdf(new_payment_id, selected_child, selected_fee_record, payment_method)

            return redirect(url_for('parent.make_payment', payment_successful=True))  # Redirect after success

        return render_template('parent/make_payment.html',
                              selected_child=selected_child,
                              unpaid_fees=unpaid_fees,
                              fee_record=fee_record,
                              total_penalty=total_penalty,
                              no_payment_due=no_payment_due,
                              payment_successful=request.args.get('payment_successful'))  # Pass success flag

    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error_message=str(e))

def generate_receipt_pdf(payment_history_id, selected_child, fee_record, payment_method):
    try:
        # Define the file path
        receipt_folder = os.path.join(os.getcwd(), 'app', 'archives', 'receipts')
        if not os.path.exists(receipt_folder):
            os.makedirs(receipt_folder)

        receipt_filename = f"receipt_{payment_history_id}.pdf"
        receipt_path = os.path.join(receipt_folder, receipt_filename)

        # Create PDF object
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Add logo at the top
        logo_path = os.path.join(os.getcwd(), 'app', 'static', 'logo.png')
        pdf.image(logo_path, x=10, y=8, w=30)

        # Title and receipt info
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(0, 102, 204)  # Blue for title
        pdf.cell(200, 10, txt="Payment Receipt", ln=True, align='C')
        pdf.ln(20)  # Increased space after title

        # Date and Payment ID section, now moved down
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(0, 0, 0)  # Black for the rest
        pdf.cell(100, 10, f"Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(100, 10, f"Receipt ID: receipt_{payment_history_id}", ln=True)
        pdf.ln(10)  # Line break for better spacing

        # Customer Section (Child)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Child Name:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{selected_child.first_name} {selected_child.last_name}", ln=True)
        pdf.ln(5)  # Line break

        # Fee Description
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Fee Description:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{fee_record.assignment.structure.description}", ln=True)
        pdf.ln(5)

        # Payment Details (Amount and Penalty)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Amount Paid:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"RM {fee_record.total_amount}", ln=True)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Penalty:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"RM {fee_record.late_fee_amount}", ln=True)
        pdf.ln(5)

        # Payment Method
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Payment Method:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{payment_method}", ln=True)
        pdf.ln(5)

        # Footer Section with Thank You
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(150, 150, 150)  # Light gray color for footer
        pdf.cell(200, 10, txt="Thank you for your payment!", ln=True, align='C')
        pdf.ln(5)  # Space at the bottom of the receipt

        # Save the PDF
        pdf.output(receipt_path)

    except Exception as e:
        print(f"Error generating receipt PDF: {str(e)}")


@parent.route('/payment_history')
@login_required
@role_required('3')
def payment_history():
    try:
        # Get selected child from session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        # Fetch the selected child's details
        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        # Fetch all fee assignments for the selected child
        fee_assignments = db.session.query(StudentFeeAssignment).filter_by(student_id=selected_child.id).all()
        fee_assignment_ids = [assignment.fee_assignment_id for assignment in fee_assignments]

        if not fee_assignment_ids:
            return render_template('parent/payment_history.html', selected_child=selected_child, payment_history=[])

        # Fetch all fee records linked to those assignments
        fee_records = db.session.query(FeeRecord).filter(FeeRecord.fee_assignment_id.in_(fee_assignment_ids)).all()
        fee_record_ids = [record.fee_record_id for record in fee_records]

        if not fee_record_ids:
            return render_template('parent/payment_history.html', selected_child=selected_child, payment_history=[])

        # Fetch payment history for the selected child's fee records
        payment_history = (
            db.session.query(PaymentHistory)
            .filter(PaymentHistory.fee_record_id.in_(fee_record_ids))
            .order_by(PaymentHistory.payment_date.desc())
            .all()
        )

        # Pass the payment history to the template
        return render_template(
            'parent/payment_history.html',
            selected_child=selected_child,
            payment_history=payment_history
        )

    except Exception as e:
        logging.error(f"Error in fetching payment history: {e}")
        return render_template('error.html', error_message="An error occurred while fetching payment history.")


@parent.route('/download_receipt/<payment_history_id>')
@login_required
@role_required('3')
def download_receipt(payment_history_id):
    try:
        # Define the receipt directory
        receipt_dir = os.path.join(os.getcwd(), 'app', 'archives', 'receipts')

        # Construct the expected receipt filename
        receipt_filename = f'receipt_{payment_history_id}.pdf'
        receipt_path = os.path.join(receipt_dir, receipt_filename)

        # Check if the file exists
        if not os.path.exists(receipt_path):
            return render_template('error.html', error_message="Receipt not found.")

        # Send the file for download
        return send_from_directory(receipt_dir, receipt_filename, as_attachment=False)

    except Exception as e:
        return render_template('error.html', error_message=str(e))



@parent.route('/notification_dashboard', methods=['GET'])
@login_required
def notification_dashboard():
    # Get the selected child's ID from the session
    selected_child_id = session.get(f'selected_child_id_{current_user.id}')
    
    if not selected_child_id:
        flash('No child selected.', 'danger')
        return redirect(url_for('parent.dashboard'))

    # Fetch the selected child's details
    selected_child = db.session.query(User).filter(User.id == selected_child_id).first()

    if not selected_child:
        flash('Selected child not found.', 'danger')
        return redirect(url_for('parent.dashboard'))

    # Fetch notifications for the selected child
    notifications = (
        db.session.query(Notification)
        .filter(Notification.student_id == selected_child_id)
        .order_by(Notification.timestamp.desc())
        .all()
    )

    # Format notifications
    formatted_notifications = []
    for notification in notifications:
        # Get the teacher's name
        teacher_name = f"{notification.teacher.first_name} {notification.teacher.last_name}"

        # Get the student's name
        student_name = f"{notification.student.first_name} {notification.student.last_name}"

        # Format the timestamp into date and time
        timestamp = notification.timestamp
        date = timestamp.strftime('%Y-%m-%d')  # Format as Date
        time = timestamp.strftime('%H:%M %p')  # Format as Time

        # Append the formatted notification to the list
        formatted_notifications.append({
            "message_type": notification.message_type,
            "message_text": notification.message_text,
            "date": date,
            "time": time,
            "teacher_name": teacher_name,
            "student_name": student_name,
        })

    # Pass the formatted notifications and selected child to the template
    return render_template(
        'parent/notification_dashboard.html',
        notifications=formatted_notifications,
        selected_child=selected_child
    )



@parent.route('/ajax_notifications', methods=['GET'])
@login_required
def ajax_notifications():
    selected_child_id = session.get(f'selected_child_id_{current_user.id}')
    
    # If no child is selected, return an error message
    if not selected_child_id:
        return jsonify({"error": "No child selected"}), 400

    # Fetch the notifications for the selected child
    notifications = (
        db.session.query(Notification)
        .filter(Notification.student_id == selected_child_id)
        .order_by(Notification.timestamp.desc())
        .all()
    )

    # Prepare the notifications HTML in the desired format
    notifications_html = ""
    if notifications:
        for notification in notifications:
            # Get the teacher's name
            teacher_name = f"{notification.teacher.first_name} {notification.teacher.last_name}"

            # Format timestamp
            timestamp = notification.timestamp
            date = timestamp.strftime('%Y-%m-%d')  # Format as Date
            time = timestamp.strftime('%H:%M %p')  # Format as Time

            # Prepare HTML for the notification
            notifications_html += f"""
                <li class="list-group-item" style="background-color: #f0f8ff;">
                    <p style="text-align:center; text-transform: uppercase; font-size: 20px; margin-bottom: 10px;">
                        <strong>{notification.message_type}</strong>
                    </p>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span><strong>Date:</strong> {date}</span>
                        <span><strong>Time:</strong> {time}</span>
                        <span><strong>Sent by: </strong>Teacher {teacher_name}</span>
                    </div>
                    <p style="margin-top: 10px;">{notification.message_text}</p>
                </li>
            """
    else:
        notifications_html = '<p class="alert alert-warning">No notifications available</p>'

    return jsonify({"notifications_html": notifications_html})

