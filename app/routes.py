from flask import Blueprint, render_template
from .models import User  # Import your models

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')  # Renders a home page
