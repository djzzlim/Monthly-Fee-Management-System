from flask import render_template, request, redirect, url_for, flash, send_file
from datetime import datetime
import statistics
from flask import Blueprint, render_template, abort, redirect, url_for, send_file, request, flash
from flask_login import login_required, current_user
from functools import wraps
from .routes import role_required, app_name
from app import db
from app.models.models import Role, User, Class, ClassAssignment, StudentFeeAssignment, FeeRecord, ParentStudentRelation, PaymentHistory, PaymentStatus, Notification, Settings
from app.models.models import FeeStructure, User, ParentStudentRelation, StudentFeeAssignment, Settings, FeeRecord
from sqlalchemy.orm import joinedload
from weasyprint import HTML
from datetime import datetime, timedelta
from sqlalchemy import func
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INVOICE_DIR = os.path.join(BASE_DIR, '..', 'archives',
                           'invoices')
REPORTS_DIR = os.path.join(BASE_DIR, '..', 'archives',
                           'reports')

# Define the accountant blueprint
accountant = Blueprint('accountant', __name__)


@accountant.route('/')
@login_required
@role_required('4')
def dashboard():
    # Count of overdue invoices (due date in the past and not paid)
    overdue_invoices_count = db.session.query(FeeRecord).filter(
        FeeRecord.status_id == 'status003',
        FeeRecord.due_date < datetime.today().date()  # Due date is in the past
    ).count() or 0

    # Count invoices based on the files in the invoices directory
    invoices_count = len(
        [f for f in os.listdir(INVOICE_DIR) if f.endswith('.pdf')])

    # Pass counts and other values to the template
    return render_template(
        'accountant/accountant.html',
        overdue_invoices_count=overdue_invoices_count,
        invoices_count=invoices_count,  # Pass invoices count to the template
        app_name=app_name()
    )


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
        if fee.due_date < today and fee.status_id != "status002":  # Not paid & overdue
            fee.status_id = "status003"  # Mark as overdue
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
        new_fee_record_id = f"fr{int(last_fee_record.fee_record_id.replace('fr', '')) + 1}" if last_fee_record else "fr1"

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
        app_name=app_name()
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

    return render_template("accountant/edit_fee_record.html", fee_record=fee_record, fee_assignments=fee_assignments, app_name=app_name())


@accountant.route('/financial_reports')
@login_required
@role_required('4')
def financial_reports():
    reports = []

    # Fetch all report files from the archive
    for report_type in ["fee_collection", "financial_health", "overdue_payment"]:
        folder_path = os.path.join(REPORTS_DIR, report_type)

        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".pdf"):
                    report_id = filename.split(".")[0]  # Remove file extension

                    # Extract the full date-time part, including both date and time
                    date_time_part = filename.split(
                        "_")[-2] + "_" + filename.split("_")[-1].replace(".pdf", "")

                    # Convert the date-time part to a datetime object
                    try:
                        # Format: 'YYYY-MM-DD_HH-MM-SS' (e.g., '2025-02-05_21-29-22')
                        report_date = datetime.strptime(
                            date_time_part, '%Y-%m-%d_%H-%M-%S')
                    except ValueError:
                        print(f"Error parsing: {date_time_part}")

                    reports.append({
                        "report_id": report_id,
                        "report_type": report_type,
                        "date": report_date  # Now it's a datetime object with both date and time
                    })

    return render_template("accountant/financial_reports.html", reports=reports, app_name=app_name())


@accountant.route('/view_report/<report_id>')
@login_required
def view_report(report_id):
    # Determine the subdirectory based on report_id prefix
    if report_id.startswith("fc_"):
        report_dir = "fee_collection"
    elif report_id.startswith("fh_"):
        report_dir = "financial_health"
    elif report_id.startswith("op_"):
        report_dir = "overdue_payment"
    else:
        return redirect(url_for("accountant.financial_reports"))

    # Construct file path
    file_path = os.path.join(REPORTS_DIR, report_dir, f"{report_id}.pdf")

    # Check if file exists, then serve it inline (view in browser)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="application/pdf", as_attachment=False)
    else:
        return redirect(url_for("accountant.financial_reports"))


@accountant.route('/delete_report/<report_id>', methods=["POST"])
@login_required
def delete_report(report_id):
    # Determine the subdirectory based on report_id prefix
    if report_id.startswith("fc_"):
        report_dir = "fee_collection"
    elif report_id.startswith("fh_"):
        report_dir = "financial_health"
    elif report_id.startswith("op_"):
        report_dir = "overdue_payment"
    else:
        return redirect(url_for("accountant.financial_reports"))

    # Construct file path
    file_path = os.path.join(REPORTS_DIR, report_dir, f"{report_id}.pdf")

    # Delete the file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for("accountant.financial_reports"))


@accountant.route('/financial_reports/generate', methods=['GET', 'POST'])
@login_required
@role_required('4')
def generate_report():
    if request.method == 'POST':
        report_type = request.form.get('reportType')

        if not report_type:
            return redirect(url_for("accountant.financial_reports"))

        if report_type == "fees":
            # Redirect to date selection form
            return redirect(url_for("accountant.generate_fees_report"))
        elif report_type == "overdue":
            return generate_overdue_report()
        elif report_type == "financialHealth":
            return generate_financial_health_report()

        return redirect(url_for("accountant.financial_reports"))

    return render_template("accountant/generate_report.html", app_name=app_name())


@accountant.route('/financial_reports/generate/fee_collection_report', methods=['GET', 'POST'])
@login_required
@role_required('4')
def generate_fees_report():
    if request.method == 'GET':
        # Default date range: earliest date in FeeRecord and today's date
        earliest_record = FeeRecord.query.order_by(
            FeeRecord.date_assigned.asc()).first()
        today = datetime.today().date()

        # Set default date range values
        start_date = earliest_record.date_assigned if earliest_record else today
        end_date = today

        # Query for fee records based on default date range
        fee_records = FeeRecord.query.filter(
            FeeRecord.status_id == "status002",  # Only include paid fees
            FeeRecord.payment_histories.any(),  # Ensure there is at least one payment
            FeeRecord.date_assigned >= start_date,
            FeeRecord.date_assigned <= end_date
        ).all()

        # Show the date selection page with fee records for the default range
        return render_template("accountant/fee_collection_report.html", start_date=start_date, end_date=end_date, fee_records=fee_records, app_name=app_name())

    elif request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if not start_date or not end_date:
            return redirect(url_for("accountant.generate_fees_report"))

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return redirect(url_for("accountant.generate_fees_report"))

        if start_date > end_date:
            return redirect(url_for("accountant.generate_fees_report"))

        # Query for fee records in the selected date range
        fee_records = FeeRecord.query.filter(
            FeeRecord.status_id == "status002",  # Only include paid fees
            FeeRecord.payment_histories.any(),  # Ensure there is at least one payment
            FeeRecord.date_assigned >= start_date,
            FeeRecord.date_assigned <= end_date
        ).all()

        # If the action is "generate", generate the PDF report
        if request.form.get('action') == 'generate':
            # Generate report logic (same as before)
            report_html = render_template(
                "accountant/fee_collection_report_pdf.html", fee_records=fee_records, datetime=datetime, app_name=app_name())
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            report_filename = f"fc_{timestamp}.pdf"
            report_path = os.path.join(
                REPORTS_DIR, "fee_collection", report_filename)
            HTML(string=report_html).write_pdf(report_path)

            # Redirect to the financial reports page after report is generated
            return redirect(url_for('accountant.financial_reports'))

        # Show the date selection page with fee records for the selected range
        return render_template("accountant/fee_collection_report.html", start_date=start_date, end_date=end_date, fee_records=fee_records, app_name=app_name())


@accountant.route('/financial_reports/generate/overdue_report', methods=['GET', 'POST'])
@login_required
@role_required('4')  # Assuming only accountants can generate reports
def generate_overdue_report():
    if request.method == 'GET':
        # Default date range: earliest overdue record and today's date
        earliest_overdue = FeeRecord.query.filter(
            FeeRecord.due_date < datetime.today().date(),
            FeeRecord.status_id != "status002"  # Exclude fully paid fees
        ).order_by(FeeRecord.due_date.asc()).first()

        today = datetime.today().date()
        start_date = earliest_overdue.due_date if earliest_overdue else today
        end_date = today

        # Query overdue fee records
        overdue_records = FeeRecord.query.filter(
            FeeRecord.due_date < end_date,
            FeeRecord.status_id == "status003"  # Exclude fully paid fees
        ).all()

        return render_template(
            "accountant/overdue_fee_report.html",
            start_date=start_date,
            end_date=end_date,
            overdue_records=overdue_records, 
            app_name=app_name()
        )

    elif request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if not start_date or not end_date:
            return redirect(url_for("accountant.generate_overdue_report"))

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return redirect(url_for("accountant.generate_overdue_report"))

        if start_date > end_date:
            return redirect(url_for("accountant.generate_overdue_report"))

        # Query for overdue fee records in the selected date range
        overdue_records = FeeRecord.query.filter(
            FeeRecord.due_date >= start_date,
            FeeRecord.due_date <= end_date,
            FeeRecord.status_id != "status002"  # Exclude fully paid fees
        ).all()

        # If the action is "generate", generate the PDF report
        if request.form.get('action') == 'generate':
            report_html = render_template(
                "accountant/overdue_fee_report_pdf.html",
                overdue_records=overdue_records,
                datetime=datetime,
                app_name=app_name()
            )
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            report_filename = f"op_{timestamp}.pdf"
            report_path = os.path.join(
                REPORTS_DIR, "overdue_payment", report_filename)
            HTML(string=report_html).write_pdf(report_path)

            # Redirect to financial reports page after report generation
            return redirect(url_for('accountant.financial_reports'))

        return render_template(
            "accountant/overdue_fee_report.html",
            start_date=start_date,
            end_date=end_date,
            overdue_records=overdue_records, 
            app_name=app_name()
        )


@accountant.route('/financial_reports/generate/financial_health_report', methods=['GET', 'POST'])
@login_required
@role_required('4')  # Only accountants can generate reports
def generate_financial_health_report():
    if request.method == 'GET':
        # Default date range
        earliest_record = FeeRecord.query.order_by(
            FeeRecord.date_assigned.asc()).first()
        today = datetime.today().date()
        start_date = earliest_record.date_assigned if earliest_record else today
        end_date = today

        statistics = calculate_financial_statistics(start_date, end_date)

        return render_template("accountant/financial_health_report.html",
                               start_date=start_date, end_date=end_date, statistics=statistics, app_name=app_name())

    elif request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if not start_date or not end_date:
            return redirect(url_for("accountant.generate_financial_health_report"))

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return redirect(url_for("accountant.generate_financial_health_report"))

        if start_date > end_date:
            return redirect(url_for("accountant.generate_financial_health_report"))

        statistics = calculate_financial_statistics(start_date, end_date)

        if request.form.get('action') == 'generate':
            report_html = render_template("accountant/financial_health_report_pdf.html",
                                          statistics=statistics, datetime=datetime, app_name=app_name())
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            report_filename = f"fh_{timestamp}.pdf"
            report_path = os.path.join(
                REPORTS_DIR, "financial_health", report_filename)
            HTML(string=report_html).write_pdf(report_path)

            return redirect(url_for('accountant.financial_reports'))

        return render_template("accountant/financial_health_report.html",
                               start_date=start_date, end_date=end_date, statistics=statistics, app_name=app_name())


def get_past_total_collected(start_date, end_date):
    """
    Retrieves total collected revenue from the previous period (e.g., last year).
    Adjusts the past date range based on the current date selection.
    """
    past_start_date = start_date - timedelta(days=(end_date - start_date).days)
    past_end_date = start_date

    past_fee_records = FeeRecord.query.filter(
        FeeRecord.date_assigned >= past_start_date,
        FeeRecord.date_assigned <= past_end_date
    ).all()

    return float(sum(record.total_amount for record in past_fee_records))


def calculate_financial_statistics(start_date, end_date):
    fee_records = FeeRecord.query.filter(
        FeeRecord.date_assigned >= start_date,
        FeeRecord.date_assigned <= end_date
    ).all()

    # Convert Decimal to float to prevent TypeError
    total_collected = float(sum(record.total_amount for record in fee_records))
    total_outstanding = float(sum(record.amount_due for record in fee_records))
    total_discounts = float(
        sum(record.discount_amount for record in fee_records))
    late_fees_collected = float(
        sum(record.late_fee_amount for record in fee_records))
    net_revenue = total_collected - total_discounts

    # Overdue Analysis
    today = datetime.today().date()
    overdue_30 = float(sum(record.amount_due for record in fee_records if 0 <= (
        today - record.due_date).days <= 30))
    overdue_60 = float(sum(record.amount_due for record in fee_records if 31 <= (
        today - record.due_date).days <= 60))
    overdue_90 = float(sum(record.amount_due for record in fee_records if 61 <= (
        today - record.due_date).days <= 90))
    overdue_90_plus = float(sum(record.amount_due for record in fee_records if (
        today - record.due_date).days > 90))

    # Statistical Analysis
    all_payments = [float(record.total_amount) for record in fee_records]

    if all_payments:
        average_collected = sum(all_payments) / len(all_payments)
        median_collected = statistics.median(all_payments)
        highest_payment = max(all_payments)
        lowest_payment = min(all_payments)
        std_dev = round(statistics.stdev(all_payments),
                        2) if len(all_payments) > 1 else 0
    else:
        average_collected = median_collected = highest_payment = lowest_payment = std_dev = 0

    # Performance Metrics
    collection_efficiency = round((total_collected / (total_collected + total_outstanding)) * 100, 2) \
        if (total_collected + total_outstanding) > 0 else 0

    compliance_rate = round(
        (len([r for r in fee_records if r.status.status_name == "Paid"]
             ) / len(fee_records)) * 100, 2
    ) if fee_records else 0

    previous_period_collected = get_past_total_collected(start_date, end_date)
    if previous_period_collected > 0:
        revenue_growth = round(
            ((total_collected - previous_period_collected) / previous_period_collected) * 100, 2)
    else:
        revenue_growth = 0  # No past data to compare

    # Recommendations
    recommendations = []
    if collection_efficiency < 80:
        recommendations.append(
            "Collection efficiency is below target. Implement stricter follow-ups on overdue payments.")
    if total_outstanding > total_collected * 0.5:
        recommendations.append(
            "Outstanding fees are high. Consider offering installment plans or discounts for early payments.")
    if compliance_rate < 75:
        recommendations.append(
            "Low compliance rate detected. Send payment reminders to increase timely payments.")
    if revenue_growth < 0:
        recommendations.append(
            "Revenue is declining. Evaluate tuition pricing and explore new income sources.")

    recommendations_text = " ".join(
        recommendations) if recommendations else "Financial performance is stable."

    return {
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "total_discounts": total_discounts,
        "late_fees_collected": late_fees_collected,
        "net_revenue": net_revenue,

        # Overdue breakdown
        "overdue_30": overdue_30,
        "overdue_60": overdue_60,
        "overdue_90": overdue_90,
        "overdue_90_plus": overdue_90_plus,

        # Statistical analysis
        "average_collected": round(average_collected, 2),
        "median_collected": round(median_collected, 2),
        "highest_payment": highest_payment,
        "lowest_payment": lowest_payment,
        "std_dev": std_dev,

        # Performance metrics
        "collection_efficiency": collection_efficiency,
        "compliance_rate": compliance_rate,
        "revenue_growth": revenue_growth,

        # Recommendations
        "recommendations": recommendations_text
    }


@accountant.route('/generate_invoices', methods=['GET', 'POST'])
@login_required
@role_required('4')
def generate_invoices():
    invoices = []
    today = datetime.today().date()

    # Find the earliest invoice date based on file modification times
    invoice_files = [
        os.path.join(INVOICE_DIR, f) for f in os.listdir(INVOICE_DIR)
        if f.startswith("invoice_") and f.endswith(".pdf")
    ]

    earliest_invoice_date = min(
        (datetime.fromtimestamp(os.path.getmtime(f)).date()
         for f in invoice_files),
        default=today  # If no invoices exist, default to today
    )

    # Default values
    start_date = earliest_invoice_date
    end_date = today

    if request.method == 'POST':
        try:
            start_date = datetime.strptime(
                request.form.get('start_date'), "%Y-%m-%d").date()
            end_date = datetime.strptime(
                request.form.get('end_date'), "%Y-%m-%d").date()

            if start_date > end_date:
                return redirect(url_for('accountant.generate_invoices'))

        except ValueError:
            return redirect(url_for('accountant.generate_invoices'))

    # Always fetch invoices for the selected/default date range
    for filename in os.listdir(INVOICE_DIR):
        if filename.startswith("invoice_") and filename.endswith(".pdf"):
            file_path = os.path.join(INVOICE_DIR, filename)
            file_time = datetime.fromtimestamp(
                os.path.getmtime(file_path)).date()

            if start_date <= file_time <= end_date:
                invoices.append({
                    "invoice_id": filename[:-4],  # Remove '.pdf' extension
                    "date": file_time
                })

    return render_template(
        "accountant/invoices.html",
        invoices=invoices,
        # Ensure date appears in input fields
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"), 
        app_name=app_name()
    )


@accountant.route('/view_invoice/<invoice_id>')
@login_required
def view_invoice(invoice_id):
    file_path = os.path.join(INVOICE_DIR, f"{invoice_id}.pdf")

    if os.path.exists(file_path):
        return send_file(file_path, mimetype="application/pdf", as_attachment=False)
    else:
        return redirect(url_for("accountant.generate_invoices"))


@accountant.route('/delete_invoice/<invoice_id>', methods=['POST'])
@login_required
@role_required('4')
def delete_invoice(invoice_id):
    file_path = os.path.join(INVOICE_DIR, f"{invoice_id}.pdf")

    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(url_for("accountant.generate_invoices"))


@accountant.route('/create_invoice', methods=['GET', 'POST'])
@login_required
@role_required('4')
def create_invoice():
    if request.method == 'POST':
        fee_record_id = request.form.get('fee_record_id')
        fee_record = FeeRecord.query.get(fee_record_id)

        if not fee_record:
            return redirect(url_for('accountant.create_invoice'))

        # Fetch required data
        student = fee_record.assignment.student
        parents = [relation.parent for relation in student.student_relations]
        invoice_date = datetime.now()
        due_date = fee_record.due_date
        fee_structure = fee_record.assignment.structure
        total_fee = fee_record.amount_due
        discounts = fee_record.discount_amount
        late_fee_amount = fee_record.late_fee_amount
        final_amount_due = fee_record.total_amount
        overdue_months = max(0, (invoice_date.date() - due_date).days // 30)

        # Render HTML for the invoice
        rendered_html = render_template("accountant/invoice_pdf.html",
                                        invoice_id=fee_record_id,
                                        invoice_date=invoice_date,
                                        due_date=due_date,
                                        student=student,
                                        parents=parents,
                                        fee_structure=fee_structure,
                                        total_fee=total_fee,
                                        discounts=discounts,
                                        late_fee_amount=late_fee_amount,
                                        final_amount_due=final_amount_due,
                                        overdue_months=overdue_months,
                                        kindergarten_name="Your Kindergarten Name",
                                        address="Your Kindergarten Address",
                                        smtp_email="contact@kindergarten.com",
                                        contact_number="+60 12-345 6789",
                                        current_year=datetime.now().year,
                                        app_name=app_name())

        # Save PDF without opening it
        pdf_path = os.path.join(INVOICE_DIR, f"invoice_{fee_record_id}.pdf")
        HTML(string=rendered_html).write_pdf(pdf_path)

        # Redirect back to the invoice list
        return redirect(url_for('accountant.generate_invoices'))

    return render_template("accountant/create_invoice.html", fee_records=FeeRecord.query.all(), app_name=app_name())


@accountant.route('/overdue_records', methods=['GET', 'POST'])
@login_required
@role_required('4')
def overdue_records():
    today = datetime.today().date()

    # Fetch overdue fee records (where due date has passed and not paid)
    overdue_fees = FeeRecord.query.filter(
        FeeRecord.due_date < today,  # Due date has passed
        FeeRecord.status_id == "status003"  # Not marked as "Paid"
    ).all()

    if request.method == 'POST':
        fee_record_id = request.form.get('fee_record_id')
        fee_record = FeeRecord.query.get(fee_record_id)

        if fee_record:
            fee_record.flagged_for_followup = 1  # Mark as flagged
            db.session.commit()
            flash("Fee record flagged for follow-ups.", "success")

        return redirect(url_for('accountant.overdue_records'))

    return render_template("accountant/overdue_records.html", overdue_fees=overdue_fees, app_name=app_name())
