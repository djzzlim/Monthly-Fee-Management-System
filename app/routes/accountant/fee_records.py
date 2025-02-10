from app import db
from flask import render_template, request, redirect, url_for
from datetime import datetime
from flask import render_template, redirect, url_for, request
from flask_login import login_required
from app.routes.routes import role_required, app_name
from . import accountant
from app.models.models import User, StudentFeeAssignment, FeeRecord, PaymentStatus, Settings, FeeStructure
from datetime import datetime


@accountant.route('/fee_records')
@login_required
@role_required('4')
def fee_records():
    today = datetime.today().date()

    # Fetch all fee records with related data
    fee_records = (
        db.session.query(FeeRecord, StudentFeeAssignment,
                         User, FeeStructure, PaymentStatus)
        .join(StudentFeeAssignment, FeeRecord.fee_assignment_id == StudentFeeAssignment.fee_assignment_id)
        .join(User, StudentFeeAssignment.student_id == User.id)
        .join(FeeStructure, StudentFeeAssignment.structure_id == FeeStructure.structure_id)
        .join(PaymentStatus, FeeRecord.status_id == PaymentStatus.status_id, isouter=True)
        .all()
    )

    # Check and update overdue statuses
    for fee, _, _, _, _ in fee_records:
        # Calculate the difference in days between today and the due date
        overdue_days = (today - fee.due_date).days

        if overdue_days > 30 and fee.status_id != "status002":  # Only mark overdue if more than 30 days
            fee.status_id = "status003"  # Mark as overdue
            db.session.commit()
        elif overdue_days <= 30 and fee.status_id != "status002":
            fee.status_id = "status001"  # Mark as unpaid
            db.session.commit()

    return render_template("accountant/fee_records.html", fee_records=fee_records, app_name=app_name())


@accountant.route('/fee_records/delete/<fee_record_id>', methods=['POST'])
@login_required
@role_required('4')
def delete_fee_record(fee_record_id):
    fee_record = FeeRecord.query.get(fee_record_id)

    if not fee_record:
        return redirect(url_for('accountant.fee_records'))

    try:
        db.session.delete(fee_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('accountant.fee_records'))


@accountant.route('/fee_records/add', methods=['GET', 'POST'])
@login_required
@role_required('4')
def add_fee_records():
    today = datetime.today().date()

    # Fetch fee assignments for dropdown
    fee_assignments = (
        db.session.query(StudentFeeAssignment, User, FeeStructure)
        .join(User, StudentFeeAssignment.student_id == User.id)
        .join(FeeStructure, StudentFeeAssignment.structure_id == FeeStructure.structure_id)
        .all()
    )

    # Fetch settings values (ensure defaults are always assigned)
    late_fee_setting = Settings.query.filter_by(
        setting_key='late_fee_amount').first()
    discount_setting = Settings.query.filter_by(
        setting_key='discount_amount').first()

    late_fee_increment = float(
        late_fee_setting.setting_value) if late_fee_setting and late_fee_setting.setting_value else 100.0
    discount_increment = float(
        discount_setting.setting_value) if discount_setting and discount_setting.setting_value else 10.0

    if request.method == 'POST':
        fee_assignment_id = request.form.get('fee_assignment_id')
        penalty = float(request.form.get('penalty', 0))
        discount = float(request.form.get('discount', 0))
        due_date = datetime.strptime(
            request.form.get('due_date'), '%Y-%m-%d').date()

        # Fetch the Fee Assignment
        assignment = StudentFeeAssignment.query.get(fee_assignment_id)
        if not assignment:
            return redirect(url_for('accountant.add_fee_records'))

        tuition_fee = float(assignment.structure.total_fee)
        total_amount = max(tuition_fee + penalty - discount, 0)

        # Generate Fee Record ID
        last_fee_record = FeeRecord.query.order_by(
            FeeRecord.fee_record_id.desc()).first()
        if last_fee_record:
            last_id = int(last_fee_record.fee_record_id.replace('fr', ''))
            new_fee_record_id = f"fr{last_id + 1}"
        else:
            new_fee_record_id = "fr1"

        # Ensure the ID doesn't already exist (important!)
        while FeeRecord.query.filter_by(fee_record_id=new_fee_record_id).first():
            last_id += 1
            new_fee_record_id = f"fr{last_id}"

        # Determine initial status
        initial_status = "status003" if due_date < today else "status001"

        # Create a new FeeRecord
        fee_record = FeeRecord(
            fee_record_id=new_fee_record_id,
            fee_assignment_id=fee_assignment_id,
            status_id=initial_status,
            date_assigned=today,
            due_date=due_date,
            amount_due=tuition_fee,
            late_fee_amount=penalty,
            discount_amount=discount,
            total_amount=total_amount,
            last_updated_date=today
        )

        db.session.add(fee_record)
        db.session.commit()

        return redirect(url_for('accountant.fee_records'))

    return render_template(
        'accountant/add_fee_record.html',
        fee_assignments=fee_assignments,
        app_name=app_name(),
        late_fee_increment=late_fee_increment,
        discount_increment=discount_increment
    )


@accountant.route('/fee_records/edit/<fee_record_id>', methods=['GET', 'POST'])
@login_required
@role_required('4')
def edit_fee_record(fee_record_id):
    fee_record = FeeRecord.query.get(fee_record_id)

    if not fee_record:
        return redirect(url_for('accountant.fee_records'))

    # Fetch fee assignments for dropdown
    fee_assignments = (
        db.session.query(StudentFeeAssignment, User, FeeStructure)
        .join(User, StudentFeeAssignment.student_id == User.id)
        .join(FeeStructure, StudentFeeAssignment.structure_id == FeeStructure.structure_id)
        .all()
    )

    # Fetch settings values
    late_fee_setting = Settings.query.filter_by(
        setting_key='late_fee_amount').first()
    discount_setting = Settings.query.filter_by(
        setting_key='discount_amount').first()

    late_fee_increment = float(
        late_fee_setting.setting_value) if late_fee_setting and late_fee_setting.setting_value else 100.0
    discount_increment = float(
        discount_setting.setting_value) if discount_setting and discount_setting.setting_value else 10.0

    if request.method == 'POST':
        try:
            fee_record.fee_assignment_id = request.form.get(
                "fee_assignment_id")
            fee_record.amount_due = float(request.form.get(
                "amount_due", fee_record.amount_due))
            fee_record.late_fee_amount = float(
                request.form.get("penalty", fee_record.late_fee_amount))
            fee_record.discount_amount = float(
                request.form.get("discount", fee_record.discount_amount))
            fee_record.total_amount = max(
                fee_record.amount_due + fee_record.late_fee_amount - fee_record.discount_amount, 0)
            fee_record.due_date = datetime.strptime(
                request.form.get("due_date"), '%Y-%m-%d').date()
            fee_record.last_updated_date = datetime.today().date()  # Update last updated date

            db.session.commit()
            return redirect(url_for("accountant.fee_records"))

        except Exception as e:
            db.session.rollback()

    return render_template(
        "accountant/edit_fee_record.html",
        fee_record=fee_record,
        fee_assignments=fee_assignments,
        app_name=app_name(),
        late_fee_increment=late_fee_increment,
        discount_increment=discount_increment
    )
