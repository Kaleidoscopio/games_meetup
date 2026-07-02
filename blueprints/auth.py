"""
blueprints/auth.py
-------------------
Registration, login/logout and "forgot password" flow.
"""

from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import _

from extensions import db
from models import User
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from utils.email_utils import send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("listings.browse"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Uniqueness checks beyond the DB constraint, so we can show a
        # friendly message instead of a raw integrity error.
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash(_("An account with that email already exists."), "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(username=form.username.data).first():
            flash(_("That username is taken, please choose another."), "danger")
            return render_template("auth/register.html", form=form)

        user = User(username=form.username.data.strip(), email=form.email.data.lower().strip())
        user.set_password(form.password.data)

        # First user matching INITIAL_ADMIN_EMAIL (if configured)
        # becomes an admin automatically - a zero-cost way to bootstrap
        # the admin panel without manual DB edits.
        configured_admin_email = current_app.config.get("INITIAL_ADMIN_EMAIL", "").lower()
        if configured_admin_email and user.email == configured_admin_email:
            user.is_admin = True
        # If no admin exists at all yet, make the very first registered
        # user an admin so the app is never left without one.
        elif User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(_("Welcome to Games Meetup! Your account has been created."), "success")
        return redirect(url_for("listings.browse"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("listings.browse"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid email or password."), "danger")
            return render_template("auth/login.html", form=form)

        remember = bool(request.form.get("remember_me"))
        login_user(user, remember=remember)
        flash(_("Welcome back, %(username)s!", username=user.username), "success")

        next_page = request.args.get("next")
        return redirect(next_page or url_for("listings.browse"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash(_("You have been logged out."), "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        # Always show the same message, whether or not the account
        # exists, so we don't leak which emails are registered.
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(user, reset_url)

        flash(_("If that email is registered, a reset link has been sent."), "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if user is None or not user.verify_reset_token(token):
        flash(_("That password reset link is invalid or has expired."), "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash(_("Your password has been reset. Please log in."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, token=token)
