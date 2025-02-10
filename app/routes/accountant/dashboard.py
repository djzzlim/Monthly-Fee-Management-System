from flask import render_template
from flask_login import login_required
from app import db
from . import accountant
from app.routes.routes import role_required, app_name
from app.models.models import FeeRecord
from datetime import datetime
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INVOICE_DIR = os.path.join(BASE_DIR, '..', '..', 'archives',
                           'invoices')

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
