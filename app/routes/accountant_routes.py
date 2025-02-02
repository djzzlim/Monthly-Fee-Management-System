from flask import Blueprint, render_template, abort, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from functools import wraps
from .routes import role_required, app_name
from app import db
from app.models.models import FeeRecord
from weasyprint import HTML
import os

INVOICE_DIR = 'archives/invoices/pending_approval/'

# Define the accountant blueprint
accountant = Blueprint('accountant', __name__)

# Route for the accountant dashboard


@accountant.route('/')
@login_required
@role_required('4')
def dashboard():
    # Calculate total fees: Sum of all fees (amount_due)
    total_fees = db.session.query(db.func.sum(FeeRecord.amount_paid)).scalar()

    # Calculate overdue fees: Sum of overdue fees (where due_date < current date and amount_due > amount_paid)
    overdue_fees = db.session.query(db.func.sum(FeeRecord.amount_due - FeeRecord.amount_paid)) \
        .filter(FeeRecord.due_date < db.func.current_date(), FeeRecord.amount_due > FeeRecord.amount_paid) \
        .scalar()

    # Count of invoices generated: Total number of invoices created
    invoices_generated = db.session.query(Invoice).count()

    # Format the currency to RM and 2 decimal places
    total_fees = f"RM {total_fees:,.2f}" if total_fees is not None else "RM 0.00"
    overdue_fees = f"RM {overdue_fees:,.2f}" if overdue_fees is not None else "RM 0.00"

    return render_template('accountant/accountant.html',
                           total_fees=total_fees,
                           overdue_fees=overdue_fees,
                           invoices_generated=invoices_generated,
                           app_name=app_name())

# Route for Fee Records


@accountant.route('/fee_records')
@login_required
@role_required('4')
def fee_records():
    fee_records = FeeRecord.query.all()
    return render_template('accountant/fee_records.html', fee_records=fee_records, app_name=app_name())

# Route for Track Overdue Accounts


@accountant.route('/track_overdue_accounts')
@login_required
@role_required('4')
def track_overdue_accounts():
    return render_template('accountant/track_overdue_accounts.html', app_name=app_name())


@accountant.route('/fee_records/<string:fee_id>')
@login_required
@role_required('4')
def fee_record_detail(fee_id):
    # Query the database for the specific fee record by `fee_id`
    fee_record = FeeRecord.query.filter_by(fee_id=fee_id).first()

    # If the fee record is not found, return a 404 error
    if not fee_record:
        abort(404)

    # Render the template with the fee record details
    return render_template('accountant/fee_record_detail.html', fee_record=fee_record, app_name=app_name())


@accountant.route('/generate_invoice/<string:invoice_id>', methods=['GET'])
@login_required
@role_required('4')
def generate_invoice(invoice_id):
    # Fetch the invoice and related fee records from the database
    invoice = Invoice.query.get(invoice_id)
    fee_records = FeeRecord.query.filter_by(invoice_id=invoice_id).all()

    if not invoice:
        return "Invoice not found", 404

    # Render the template to generate the invoice as HTML
    html_content = render_template(
        'accountant/invoice.html', invoice=invoice, fee_records=fee_records)

    # Use WeasyPrint to convert the HTML to PDF
    pdf = HTML(string=html_content).write_pdf()

    # Define the file path to save the generated PDF
    file_path = os.path.join(INVOICE_DIR, f"invoice_{invoice_id}.pdf")

    # Ensure the directory exists
    os.makedirs(INVOICE_DIR, exist_ok=True)

    # Save the PDF to the disk
    with open(file_path, 'wb') as f:
        f.write(pdf)

    # Open the PDF in the browser by setting the content disposition to 'inline'
    return send_file(file_path, as_attachment=False, mimetype='application/pdf')


@accountant.route('/generate_invoices', methods=['GET'])
@login_required
@role_required('4')
def generate_invoices():
    # Fetch a list of invoices (you can filter or paginate as needed)
    invoices = Invoice.query.all()
    return render_template('accountant/generate_invoices.html', invoices=invoices, app_name=app_name())


@accountant.route('/edit_invoice/<string:invoice_id>', methods=['GET', 'POST'])
@login_required
@role_required('4')
def edit_invoice(invoice_id):
    # Fetch the invoice from the database
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return "Invoice not found", 404

    if request.method == 'POST':
        # Update the invoice details from the form
        invoice.total_amount = request.form.get('total_amount')
        # Add other fields as necessary (e.g., due_date, status, etc.)

        # Commit the changes to the database
        db.session.commit()

        # Redirect back to the Generate Invoices page
        return redirect(url_for('accountant.generate_invoices'))

    # Render the edit form with the current invoice data
    return render_template('accountant/edit_invoice.html', invoice=invoice, app_name=app_name())
