import random
from flask import Blueprint, flash, jsonify, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from .routes import role_required
from ..models.models import User, ParentStudentRelation, StudentFeeAssignment, FeeStructure, FeeRecord, Settings, PaymentHistory  # Adjust import paths as needed
from weasyprint import HTML
from io import BytesIO
from flask import Response
import datetime
import logging
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

        # Fetch the selected child's details from the database
        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        # Fetch the fee assignments related to the selected child
        fee_assignments = db.session.query(StudentFeeAssignment).filter_by(student_id=selected_child_id).all()

        # Fetch fee records for all the fee assignments
        fee_records = []
        for assignment in fee_assignments:
            records = db.session.query(FeeRecord).filter_by(fee_assignment_id=assignment.fee_assignment_id).all()
            fee_records.extend(records)

        # Initialize variables for the summary
        total_amount_due = 0
        total_penalty = 0
        current_date = datetime.datetime.now().date()  # Define current_date here

        # Process each fee record
        for record in fee_records:
            # Only consider unpaid (status001) or overdue (status003) fees
            if record.status and record.status.status_id != "status002":  # Exclude "Paid" status
                total_amount_due += record.amount_due

                # Calculate penalty if the fee is overdue
                if current_date > record.due_date:
                    days_late = (current_date - record.due_date).days
                    penalty = days_late * 5  # Assuming 5 units per day penalty
                    record.penalty = penalty
                    total_penalty += penalty

        # Calculate the total amount (Amount Due + Penalty)
        total_amount_with_penalty = total_amount_due + total_penalty

        return render_template(
            'parent/fee_summary.html',
            selected_child=selected_child,
            fee_records=fee_records,
            total_amount_due=total_amount_due,
            total_penalty=total_penalty,
            total_amount_with_penalty=total_amount_with_penalty,
            current_date=current_date  # Pass current_date to the template
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

        # Fetch fee records and associated invoice details
        fee_records = []
        for assignment in fee_assignments:
            records = db.session.query(FeeRecord).filter_by(fee_assignment_id=assignment.fee_assignment_id).all()

            # For each fee record, get the invoice details (if any)
            for record in records:
                invoice = db.session.query(Invoice).filter_by(fee_record_id=record.fee_record_id).first()
                if invoice:
                    record.invoice_id = invoice.invoice_id
                    record.date_assigned = invoice.invoice_date

            fee_records.extend(records)

        # Initialize totals
        total_amount_due = 0
        total_penalty = 0
        current_date = datetime.datetime.now().date()

        for record in fee_records:
            if record.status and record.status.status_id != "status002":  # Exclude "Paid" status
                total_amount_due += record.amount_due
                if current_date > record.due_date:
                    days_late = (current_date - record.due_date).days
                    penalty = days_late * 5  # Assuming a penalty of 5 units/day
                    record.penalty = penalty
                    total_penalty += penalty

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


@parent.route('/print_invoice/<int:fee_record_id>')
@login_required
@role_required('3')
def print_invoice(fee_record_id):
    try:
        logging.info(f"Fetching fee record with ID: {fee_record_id}")
        
        # Retrieve the fee record by its ID
        fee_record = db.session.query(FeeRecord).filter_by(id=fee_record_id).first()

        if not fee_record:
            logging.error(f"Fee record with ID {fee_record_id} not found.")
            return render_template('error.html', error_message="Fee record not found.")

        # Retrieve the invoice associated with the fee record
        invoice = db.session.query(Invoice).filter_by(fee_record_id=fee_record.fee_record_id).first()

        if not invoice:
            logging.error(f"Invoice not found for fee record {fee_record_id}.")
            return render_template('error.html', error_message="Invoice not found for this fee record.")

        # Prepare the invoice data to pass to the template
        invoice_data = {
            'date_assigned': invoice.invoice_date,
            'invoice_id': invoice.invoice_id,
            'fee_type': fee_record.assignment.structure.description,
            'due_date': fee_record.due_date,
            'amount': fee_record.amount_due,
            'status': fee_record.status.status_name if fee_record.status else "Unknown",
            'balance': fee_record.balance_due,
        }

        # Render the invoice HTML template with the invoice data
        html_content = render_template('invoice_template.html', invoice_data=invoice_data)

        # Generate the PDF from the rendered HTML
        pdf = HTML(string=html_content).write_pdf()

        # Return the PDF as a response
        return Response(pdf, content_type='application/pdf', headers={'Content-Disposition': 'inline; filename="invoice.pdf"'})

    except Exception as e:
        logging.error(f"Error generating invoice: {str(e)}")
        return render_template('error.html', error_message=str(e))
    


@parent.route('/make_payment', methods=['GET', 'POST'])
@login_required
@role_required('3')
def make_payment():
    try:
        if request.method == 'POST':
            amount = request.form.get('amount')
            payment_method = request.form.get('payment_method')
            remarks = request.form.get('remarks')

            # Process payment logic (this would include saving the payment info to the database)

            return redirect(url_for('parent.payment_history'))  # Redirect to payment history page after payment

        # Get selected child from session
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()

        # Retrieve fee assignments for the selected child
        fee_assignments = (
            db.session.query(StudentFeeAssignment)
            .join(User, User.id == StudentFeeAssignment.student_id)
            .join(FeeStructure, FeeStructure.structure_id == StudentFeeAssignment.fee_structure_id)
            .join(Activity, Activity.activity_id == StudentFeeAssignment.activity_id)
            .filter(StudentFeeAssignment.student_id == selected_child_id)
            .all()
        )

        # Fetch the late fee from settings
        late_fee_amount = db.session.query(Settings).filter_by(setting_key='late_fee_amount').first()
        late_fee_amount = float(late_fee_amount.setting_value) if late_fee_amount else 0.00

        # Initialize totals
        total_fee = 0.0
        total_paid = 0.0
        total_penalty = 0.0

        # Loop through each fee assignment to calculate fees and penalties
        for fee in fee_assignments:
            total_fee += fee.fee_structure.total_fee
            total_paid += fee.fee_record.paid_amount if fee.fee_record else 0.0
            balance_due = fee.fee_structure.total_fee - (fee.fee_record.paid_amount if fee.fee_record else 0.0)

            # Calculate overdue days and late fee if overdue
            if fee.due_date and fee.due_date < db.func.current_date():
                overdue_days = (db.func.current_date() - fee.due_date).days
                penalty = late_fee_amount * overdue_days
                total_penalty += penalty

        # Calculate total due with penalty
        total_due_with_penalty = total_fee - total_paid + total_penalty

        balance_due = total_fee - total_paid
        return render_template(
            'parent/make_payment.html', 
            selected_child=selected_child,
            total_due_with_penalty=total_due_with_penalty,
            total_due=balance_due,
            total_penalty=total_penalty
        )

    except Exception as e:
        return render_template('error.html', error_message=str(e))


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
            return render_template(
                'error.html',
                error_message="Selected child not found."
            )

        # Fetch payment history for the selected child
        payment_history = (
            db.session.query(PaymentHistory)
            .filter_by(student_id=selected_child.id)
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


@parent.route('/print_receipt/<int:fee_id>')
@login_required
@role_required('3')
def print_receipt(fee_id):
    try:
        # Retrieve the fee assignment
        fee = db.session.query(StudentFeeAssignment).join(FeeStructure).filter_by(id=fee_id).first()

        if not fee:
            return render_template('error.html', error_message="Fee record not found.")

        # Generate the content for the PDF
        invoice_data = {
            'date_assigned': fee.date_assigned,
            'invoice_id': fee.invoice_id,
            'fee_type': fee.fee_structure.name,
            'due_date': fee.due_date,
            'amount': fee.fee_structure.total_fee,
            'status': 'Paid' if fee.fee_record and fee.fee_record.paid_amount == fee.fee_structure.total_fee else 'Unpaid',
            'balance': fee.fee_structure.total_fee - (fee.fee_record.paid_amount if fee.fee_record else 0),
            'amount_paid': fee.fee_record.paid_amount if fee.fee_record else 0,
            'balance_due': fee.fee_structure.total_fee - (fee.fee_record.paid_amount if fee.fee_record else 0)
        }

        # Render the receipt HTML
        html_content = render_template('parent/receipt_template.html', invoice_data=invoice_data)

        # Generate the PDF from the rendered HTML
        pdf = HTML(string=html_content).write_pdf()

        # Return the PDF as a response
        response = Response(pdf, content_type='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename=receipt_{fee.invoice_id}.pdf'

        return response

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
    messages = (
        db.session.query(Message)
        .join(User, (Message.student_id == User.id))
        .filter(Message.student_id == selected_child_id)
        .order_by(Message.timestamp.desc())  # Order messages by timestamp (latest first)
        .all()
    )

    # Format messages
    formatted_messages = []
    for message in messages:
        # Get the teacher's name
        teacher_name = f"{message.teacher.first_name} {message.teacher.last_name}"

        # Get the student's name
        student_name = f"{message.student.first_name} {message.student.last_name}"

        # Format the timestamp into date and time
        timestamp = message.timestamp
        date = timestamp.strftime('%Y-%m-%d')  # Format as Date
        time = timestamp.strftime('%H:%M %p')  # Format as Time

        # Append the formatted message to the list
        formatted_messages.append({
            "message_type": message.message_type,
            "message_text": message.message_text,
            "status": message.status,
            "date": date,
            "time": time,
            "teacher_name": teacher_name,
            "student_name": student_name,
        })

    # Pass the formatted messages and selected child to the template
    return render_template(
        'parent/notification_dashboard.html',
        messages=formatted_messages,
        selected_child=selected_child
    )



@parent.route('/ajax_notifications', methods=['GET'])
@login_required
def ajax_notifications():
    selected_child_id = session.get(f'selected_child_id_{current_user.id}')
    
    # If no child is selected, return an error message
    if not selected_child_id:
        return jsonify({"error": "No child selected"}), 400

    # Fetch the messages for the selected child
    messages = (
        db.session.query(Message)
        .filter(Message.student_id == selected_child_id)
        .order_by(Message.timestamp.desc())
        .all()
    )

    # Prepare the notifications HTML in the desired format
    notifications_html = ""
    if messages:
        for message in messages:
            
            teacher_name = f"{message.teacher.first_name} {message.teacher.last_name}"

            # Format timestamp
            timestamp = message.timestamp
            date = timestamp.strftime('%Y-%m-%d')  # Format as Date
            time = timestamp.strftime('%H:%M %p')  # Format as Time

            # Prepare HTML for the notification
            notifications_html += f"""
                <li class="list-group-item" style="background-color: #f0f8ff;">
                    <p style="text-align:center; text-transform: uppercase; font-size: 20px; margin-bottom: 10px;"><strong>{message.message_type}</strong></p>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span><strong>Date:</strong> {date}</span>
                        <span><strong>Time:</strong> {time}</span>
                        <span><strong>Sent by: </strong>Teacher {teacher_name}</span>
                    </div>
                </li>
            """
    else:
        notifications_html = '<p class="alert alert-warning">No messages available</p>'

    return jsonify({"notifications_html": notifications_html})

