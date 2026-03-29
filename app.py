import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from application.database import db

STATIC_SECRET_KEY = 'hms-static-secret-key'
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'
DEFAULT_ADMIN_EMAIL = 'rohit@gmail.com'

app = None

login_Manager = LoginManager()


def _resolve_database_uri() -> str:
    """Pick DATABASE_URL when provided, otherwise use an app-local SQLite file.

    On Vercel, the writable path is /tmp, so default there to avoid read-only errors.
    """
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    sqlite_dir = Path(os.getenv('SQLITE_DIR', '/tmp'))
    sqlite_name = os.getenv('SQLITE_FILENAME', 'homs.db')
    sqlite_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_dir / sqlite_name}"


def create_app():
    app = Flask(__name__)
    app.debug = os.getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', STATIC_SECRET_KEY)
    app.config['SQLALCHEMY_DATABASE_URI'] = _resolve_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    my_login_manager = LoginManager()
    my_login_manager.init_app(app)

    from application.models import User, Admin, Patient, Doctor, Appointment, Treatment, Department

    with app.app_context():
        db.create_all()
        db.session.commit()

        existing_admin = Admin.query.filter_by(username=DEFAULT_ADMIN_USERNAME).first()
        if not existing_admin:
            user = User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                user_role=1,
            )
            db.session.add(user)
            db.session.commit()

            admin = Admin(
                username=DEFAULT_ADMIN_USERNAME,
                password=DEFAULT_ADMIN_PASSWORD,
                admin_id=user.id,
                email=DEFAULT_ADMIN_EMAIL,
                full_name='System Administrator',
                phone='0000000001',
            )
            db.session.add(admin)
            db.session.commit()

        if Department.query.count() == 0:
            starter_departments = [
                Department(name='Cardiology', description='Heart and cardiovascular system'),
                Department(name='Neurology', description='Brain and nervous system'),
                Department(name='Orthopedics', description='Bones, joints, and muscles'),
                Department(name='Pediatrics', description='Medical care for children'),
                Department(name='Dermatology', description='Skin, hair, and nails'),
                Department(name='General Medicine', description='Primary and preventive care'),
            ]
            db.session.add_all(starter_departments)
            db.session.commit()

    @my_login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.app_context().push()

    return app


app = create_app()

from application.routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=app.debug)
