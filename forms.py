"""
forms.py
--------
WTForms classes used for every HTML form in the app. Using Flask-WTF
gives us free CSRF protection and server-side validation, which keeps
templates simple and inputs safe.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, IntegerField, SelectField, TextAreaField,
    DateField, TimeField, SubmitField, HiddenField, BooleanField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from wtforms.widgets import TextInput


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = SubmitField("Keep me signed in")  # rendered as a checkbox in the template
    submit = SubmitField("Log in")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset password")


class ListingForm(FlaskForm):
    game_name = StringField("Game name", validators=[DataRequired(), Length(max=150)])

    # Native <input type="date"> renders according to the visitor's OS/
    # browser locale (e.g. dd/mm/yyyy on a Portuguese Windows machine),
    # so it's kept as-is - it's both correct and avoids manual-entry
    # errors. <input type="time"> is less reliable across locales (some
    # show a 12-hour AM/PM picker), so that one stays as an explicit
    # 24-hour text field.
    game_date = DateField("Date", validators=[DataRequired()])
    game_time = TimeField(
        "Time",
        format="%H:%M",
        widget=TextInput(),
        validators=[DataRequired()],
        render_kw={"placeholder": "HH:MM (24-hour)", "inputmode": "numeric"},
    )

    # "shop" = pick from the pre-defined Hobby Shop list, "free" = type your own.
    location_type = SelectField(
        "Location type",
        choices=[ ("shop", "Hobby Shop - Listed below"), ("free", "Personalized location")],
        validators=[DataRequired()],
    )
    shop_id = SelectField("Hobby shop", coerce=int, validators=[Optional()])
    free_location_text = StringField("Location (address / description)", validators=[Optional(), Length(max=255)])
    region = StringField("Region", validators=[Optional(), Length(max=100)])

    players_required = IntegerField(
        "Players required", validators=[DataRequired(), NumberRange(min=1, max=100)], default=2
    )
    notes = TextAreaField("Notes (optional)", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Publish listing")


class EnrollForm(FlaskForm):
    notes = StringField("Notes (e.g. faction / deck / character)", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Join this game")


class MessageForm(FlaskForm):
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=4000)])
    submit = SubmitField("Send")


class HobbyShopForm(FlaskForm):
    name = StringField("Shop name", validators=[DataRequired(), Length(max=150)])
    region = StringField("Region", validators=[DataRequired(), Length(max=100)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    active = SelectField("Active", choices=[("1", "Yes"), ("0", "No")], default="1")
    submit = SubmitField("Save shop")