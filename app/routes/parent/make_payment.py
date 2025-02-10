# app/routes/parent/make_payment.py
from flask import render_template, redirect, url_for, session, flash, request
from flask_login import login_required, current_user
from ..routes import role_required, app_name
from app.models.models import User, StudentFeeAssignment, FeeRecord, PaymentHistory, Notification, MessageTemplate, ClassAssignment
import datetime
import pytz
import os
from fpdf import FPDF
from app import db
from . import parent

@parent.route('/make_payment', methods=['GET', 'POST'])
@login_required
@role_required('3')
def make_payment():
    try:
        user_specific_key = f'selected_child_id_{current_user.id}'
        selected_child_id = session.get(user_specific_key)

        if not selected_child_id:
            return redirect(url_for('parent.dashboard'))

        selected_child = db.session.query(User).filter_by(id=selected_child_id).first()
        if not selected_child:
            return render_template('error.html', error_message="Selected child not found.")

        unpaid_fees = (
            db.session.query(FeeRecord)
            .join(StudentFeeAssignment)
            .filter(
                StudentFeeAssignment.student_id == selected_child.id,
                FeeRecord.status_id.in_(['status001', 'status003'])
            )
            .all()
        )

        no_payment_due = len(unpaid_fees) == 0
        fee_record = unpaid_fees[0] if not no_payment_due else None
        total_penalty = fee_record.late_fee_amount if fee_record else 0

        if request.method == 'POST':
            fee_payment_id = request.form.get('fee_payment')
            payment_method = request.form.get('payment_method')
            message_type = "Payment Confirmation"  # Fixed message type

            selected_fee_record = db.session.query(FeeRecord).filter_by(fee_record_id=fee_payment_id).first()
            if not selected_fee_record:
                flash('Invalid fee selection.', 'danger')
                return redirect(url_for('parent.make_payment'))

            if not payment_method:
                flash('Please select a payment method.', 'danger')
                return redirect(url_for('parent.make_payment'))

            last_payment = db.session.query(PaymentHistory).order_by(PaymentHistory.history_id.desc()).first()
            new_number = int(last_payment.history_id[2:]) + 1 if last_payment else 1
            new_payment_id = f'ph{new_number}'

            # Malaysia Time (UTC+8)
            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            malaysia_time = datetime.datetime.now(malaysia_tz)

            new_payment = PaymentHistory(
                history_id=new_payment_id,
                fee_record_id=selected_fee_record.fee_record_id,
                amount_paid=selected_fee_record.total_amount,
                payment_method=payment_method,
                payment_date=malaysia_time,  
            )

            selected_fee_record.status_id = 'status002'
            selected_fee_record.last_updated_date = malaysia_time  # Ensure MYT is stored

            db.session.add(new_payment)
            db.session.commit()

            # Generate PDF Receipt
            generate_receipt_pdf(new_payment_id, selected_child, selected_fee_record, payment_method)

            ### Add Notification for the Parent ###
            template = db.session.query(MessageTemplate).filter_by(message_temp_id='template3').first()
            template_text = template.template_text if template else "Payment received successfully."

            # Get Teacher ID and Class Name
            student_class_assignment = db.session.query(ClassAssignment).filter_by(student_id=selected_child.id).first()
            teacher_id = student_class_assignment.teacher_id if student_class_assignment else None
            class_name = student_class_assignment.class_.class_name if student_class_assignment and student_class_assignment.class_ else "Unknown Class"

            # Get Fee Type
            fee_assignment = db.session.query(StudentFeeAssignment).join(FeeRecord).filter(
                StudentFeeAssignment.student_id == selected_child.id,
                FeeRecord.fee_record_id == selected_fee_record.fee_record_id
            ).first()
            fee_type = fee_assignment.structure.description if fee_assignment else "Unknown Fee Type"

            # Replace placeholders in message text
            message_text = template_text.format(
                amount=selected_fee_record.total_amount,
                child_name=f"{selected_child.first_name} {selected_child.last_name}",
                timestamp=malaysia_time.strftime('%Y-%m-%d %I:%M %p'),
                payment_history_id=new_payment_id,
                class_name=class_name,
                fee_type=fee_type,
                amount_paid=selected_fee_record.total_amount,
                payment_method=payment_method
            )

            # Generate Notification ID
            last_notification = db.session.query(Notification).order_by(Notification.notification_id.desc()).first()
            last_number = int(last_notification.notification_id[5:]) if last_notification else 0  
            notification_id = f'notif{last_number + 1}'

            while db.session.query(Notification).filter_by(notification_id=notification_id).first():
                last_number += 1  
                notification_id = f'notif{last_number + 1}'

            # Insert Notification Record
            new_notification = Notification(
                notification_id=notification_id,
                teacher_id=teacher_id,
                student_id=selected_child.id,
                message_type=message_type,
                message_text=message_text,
                timestamp=malaysia_time
            )

            db.session.add(new_notification)
            db.session.commit()

            return redirect(url_for('parent.make_payment', payment_successful=True, payment_history_id=new_payment_id))

        return render_template('parent/make_payment.html',
                               selected_child=selected_child,
                               unpaid_fees=unpaid_fees,
                               fee_record=fee_record,
                               total_penalty=total_penalty,
                               no_payment_due=no_payment_due,
                               payment_successful=request.args.get('payment_successful'), 
                               app_name=app_name())

    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error_message=str(e))


def generate_receipt_pdf(payment_history_id, selected_child, fee_record, payment_method):
    try:
        receipt_folder = os.path.join(os.getcwd(), 'app','archives', 'receipts')
        if not os.path.exists(receipt_folder):
            os.makedirs(receipt_folder)

        receipt_filename = f"receipt_{payment_history_id}.pdf"
        receipt_path = os.path.join(receipt_folder, receipt_filename)

        # Fetch Payment Date from Database (Already in MYT)
        payment = db.session.query(PaymentHistory).filter_by(history_id=payment_history_id).first()
        payment_date_str = payment.payment_date.strftime('%Y-%m-%d %H:%M:%S') 

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        logo_path = os.path.join(os.getcwd(), 'app', 'static', 'logo.png')
        pdf.image(logo_path, x=10, y=8, w=30)

        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(200, 10, txt="Payment Receipt", ln=True, align='C')
        pdf.ln(20)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)  
        pdf.cell(30, 10, "Date:", ln=False)

        pdf.set_font('Arial', '', 12)  
        pdf.cell(70, 10, f"{payment_date_str} MYT", ln=True)
        
        pdf.set_font('Arial', 'B', 12)  
        pdf.cell(40, 10, "Receipt ID:", ln=False)

        pdf.set_font('Arial', '', 12)  
        pdf.cell(60, 10, f"receipt_{payment_history_id}", ln=True)

        pdf.ln(10)


        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Child Name:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{selected_child.first_name} {selected_child.last_name}", ln=True)
        pdf.ln(5)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Fee Description:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{fee_record.assignment.structure.description}", ln=True)
        pdf.ln(5)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Payment Details", ln=True)
        pdf.set_font('Arial', '', 12)

        pdf.cell(100, 10, f"Amount Due:", ln=False)
        pdf.cell(100, 10, f"RM {fee_record.amount_due}", ln=True)

        pdf.cell(100, 10, f"Penalty:", ln=False)
        pdf.cell(100, 10, f"RM {fee_record.late_fee_amount}", ln=True)

        pdf.cell(100, 10, f"Discount:", ln=False)
        pdf.cell(100, 10, f"RM {fee_record.discount_amount}", ln=True)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Total Amount Due:", ln=False)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"RM {fee_record.total_amount}", ln=True)
        pdf.ln(10)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(100, 10, f"Payment Method:", ln=False)
        pdf.set_font('Arial', '', 12)
        pdf.cell(100, 10, f"{payment_method}", ln=True)
        pdf.ln(10)

        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(200, 10, txt="Thank you for your payment!", ln=True, align='C')
        pdf.ln(5)

        pdf.output(receipt_path)

    except Exception as e:
        print(f"Error generating receipt PDF: {str(e)}")