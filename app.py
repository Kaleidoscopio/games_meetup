"""
app.py
------
Application entry point. Creates and configures the Flask app using
the "app factory" pattern, registers all blueprints, and starts the
background scheduler that auto-closes stale listings.

Run locally with:
    python app.py

Or with the Flask CLI:
    flask --app app run --debug
"""

import os
from datetime import datetime

from flask import Flask, render_template, session, request, redirect, url_for
from flask_login import current_user, login_required

from config import Config
from extensions import db, login_manager, mail, csrf, scheduler, babel
from models import User
from utils.scheduler import init_scheduler

def get_locale():
    # 1. Explicit choice made earlier this session (via the switcher)
    if "language" in session:
        return session["language"]
    # 2. Signed-in user's saved preference
    if current_user.is_authenticated and current_user.locale:
        return current_user.locale
    # 3. Best match from the browser's Accept-Language header
    return request.accept_languages.best_match(Config.LANGUAGES.keys())

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure the instance/ folder (holds the SQLite file) exists.
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # --- Initialise extensions ------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Register blueprints ------------------------------------------------
    from blueprints.auth import auth_bp
    from blueprints.listings import listings_bp
    from blueprints.messaging import messaging_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(admin_bp)

    # --- Home route -----------------------------------------------------
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("listings.browse"))
        return render_template("index.html")

    # --- Language switcher ---
    @app.route("/set-language/<lang_code>")
    def set_language(lang_code):
        if lang_code in app.config["LANGUAGES"]:
            session["language"] = lang_code
            if current_user.is_authenticated:
                current_user.locale = lang_code
                db.session.commit()
        return redirect(request.referrer or url_for("index"))

    # --- Template helpers -----------------------------------------------
    # Makes `now()` and formatting helpers available in every template
    # without importing them everywhere.
    @app.context_processor
    def inject_helpers():
        unread_count = 0
        if current_user.is_authenticated:
            from models import Message
            unread_count = Message.query.filter_by(
                recipient_id=current_user.id, read_at=None
            ).count()

        from models import MaintenanceBanner
        now = datetime.utcnow()
        active_maintenance_banners = MaintenanceBanner.query.filter(
            MaintenanceBanner.starts_at <= now, MaintenanceBanner.ends_at >= now
        ).order_by(MaintenanceBanner.ends_at.asc()).all()

        return {
            "current_year": datetime.utcnow().year, 
            "unread_message_count": unread_count,
            "available_languages": app.config["LANGUAGES"],
            "get_locale": get_locale,
            "active_maintenance_banners": active_maintenance_banners,
        }

    # --- Error pages ------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    # --- Database setup + background scheduler -----------------------------
    with app.app_context():
        db.create_all()  # creates tables on first run; safe to call every start
        # Only run the scheduler in the actual serving process, not in the
        # Werkzeug reloader's parent process.
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            init_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    # debug=True is fine for local development; a production deployment
    # should use a proper WSGI server (gunicorn/waitress) - see README.
    app.run(debug=True, host="0.0.0.0", port=8002)
