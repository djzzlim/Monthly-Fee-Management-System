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
    from .routes.routes import main
    from .routes.auth import auth
    from .routes.admin_routes import admin
    from .routes.accounting_routes import accounting
    from .routes.education_routes import education
    from .routes.parent_routes import parent

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(accounting, url_prefix='/accounting')
    app.register_blueprint(education, url_prefix='/education')
    app.register_blueprint(parent, url_prefix='/parent')

    with app.app_context():
        db.create_all()  # Call with parentheses to create tables

    return app

# Define the user_loader function globally
@login_manager.user_loader
def load_user(user_id):
    from app.models.models import User  # Import here to avoid circular import
    return User.query.get(user_id)
