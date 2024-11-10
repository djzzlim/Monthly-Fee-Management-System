from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize the database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import routes
    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all

    return app
