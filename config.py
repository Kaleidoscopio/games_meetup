"""
config.py
---------
Central place for all configuration values.

Everything here is read from environment variables (with sensible
defaults for local development) so that:
  * No secrets ever get committed to source control.
  * The same code can run locally, on a free-tier host (Render,
    PythonAnywhere, Railway, etc.) or anywhere else just by setting
    environment variables.

Copy `.env.example` to `.env` and fill in real values before running
in anything other than local/dev mode.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables from a local .env file if present (does nothing in
# production if the file doesn't exist - env vars set by the host
# take precedence).
load_dotenv()

# Base directory of the project, used to build absolute file paths.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask settings -------------------------------------------------
    # Secret key used to sign session cookies / CSRF tokens.
    # MUST be overridden with a long random string in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # --- Database --------------------------------------------------------
    # SQLite is a single file on disk - zero hosting cost, no separate
    # database server needed. Perfect for a small player-to-player app.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'games_meetup.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLAlchemy Engine Options to prevent broken/stale DB socket connections
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # Verifies connection health prior to executing queries
        "pool_recycle": 1800,    # Forces recycling of connections older than 30 minutes
        "pool_size": 10,         # Keeps a baseline size for your connection pool
        "max_overflow": 5,       # Allows overflow connections during brief spikes
    }

    # --- Sessions ----------------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # --- Mail (used for password recovery + listing notifications) --------
    # Free options: a Gmail account with an "App Password" (free), or
    # any other SMTP provider with a free tier (e.g. Brevo/Sendinblue
    # free tier gives 300 emails/day at no cost).
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # If no mail credentials are configured, the app falls back to
    # printing emails to the console instead of failing - handy for
    # local development/testing without any mail account at all.
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "false").lower() == "true"

    # --- Business rules ------------------------------------------------------
    # Number of days after the game date that an open listing is
    # automatically closed by the background scheduler.
    AUTO_CLOSE_AFTER_DAYS = int(os.environ.get("AUTO_CLOSE_AFTER_DAYS", 3))

    # How often (in minutes) the background job checks for listings
    # that need to be auto-closed.
    SCHEDULER_INTERVAL_MINUTES = int(os.environ.get("SCHEDULER_INTERVAL_MINUTES", 60))

    # First user to register with this email is automatically promoted
    # to admin, so there is always a way into the admin panel without
    # touching the database by hand.
    INITIAL_ADMIN_EMAIL = os.environ.get("INITIAL_ADMIN_EMAIL", "")

    # --- Internationalization ------------------------------------------------
    LANGUAGES = {
        "en": "English",
        "pt": "Português",
        "es": "Español",
        "fr": "Français",
    }
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(BASE_DIR, "translations")