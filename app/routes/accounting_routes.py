from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Create the accounting blueprint
accounting = Blueprint('accounting', __name__)

@accounting.route('/manage_fees')
@login_required
def manage_fees():
    return render_template('accounting/manage_fees.html')

@accounting.route('/generate_invoices')
@login_required
def generate_invoices():
    return render_template('accounting/generate_invoices.html')

@accounting.route('/payment_reports')
@login_required
def payment_reports():
    return render_template('accounting/payment_reports.html')
