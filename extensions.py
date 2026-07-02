"""
extensions.py
-------------
Extension objects are created here (unbound) and initialised against
the real app inside app.py with `.init_app(app)`. This avoids circular
imports between app.py, models.py and the blueprints, since every
module can simply do `from extensions import db` etc.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
scheduler = BackgroundScheduler(daemon=True)

# Flask-Login configuration: where to send anonymous users who try to
# access a @login_required page, and the flash message category.
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
