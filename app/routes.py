from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')  # Renders a home page

@main.route('/dashboard')
@login_required  # Ensure the user is logged in
def dashboard():
    return render_template('dashboard.html')