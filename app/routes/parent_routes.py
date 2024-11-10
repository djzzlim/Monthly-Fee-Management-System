from flask import Blueprint, render_template
from flask_login import login_required

# Create the parent blueprint
parent = Blueprint('parent', __name__)

@parent.route('/fee_details')
@login_required
def fee_details():
    return render_template('parent/fee_details.html')

@parent.route('/payment_history')
@login_required
def payment_history():
    return render_template('parent/payment_history.html')

@parent.route('/make_payment')
@login_required
def make_payment():
    return render_template('parent/make_payment.html')
