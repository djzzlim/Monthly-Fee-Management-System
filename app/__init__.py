from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path, urandom
from config import Config
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
DB_NAME = "db.sqlite3"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from .routes.routes import routes
    from .routes.auth import auth
    from .routes.accountant_routes import accountant
    from .routes.admin_routes import admin
    # from .routes.education_routes import education
    # from .routes.parent_routes import parent

    app.register_blueprint(routes, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(accountant, url_prefix='/accountant')
    app.register_blueprint(admin, url_prefix='/admin')
    # app.register_blueprint(education, url_prefix='/education')
    # app.register_blueprint(parent, url_prefix='/parent')

    create_database(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Create Database!')


@login_manager.user_loader
def load_user(user_id):
    from .models.models import User
    return User.query.get(user_id)
