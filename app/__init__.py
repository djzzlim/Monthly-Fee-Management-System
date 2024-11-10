from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager
from flask_mail import Message, Mail

# Initialize the database and login manager
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)  # Initialize the database
    mail.init_app(app)
    login_manager.init_app(app)  # Initialize Flask-Login
    login_manager.login_view = 'auth.login'  # Redirect to login if not logged in

    # Import routes
    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all()  # Call with parentheses to create tables

    return app

# Define the user_loader function globally
@login_manager.user_loader
def load_user(user_id):
    from .models import User  # Import here to avoid circular import
    return User.query.get(user_id)
