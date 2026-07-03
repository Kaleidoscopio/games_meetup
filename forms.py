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
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from wtforms.widgets import TextInput
from flask_babel import lazy_gettext as _l


class RegisterForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField(_l("Email"), validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField(_l("Password"), validators=[DataRequired(), Length(min=8, message=_l("Use at least 8 characters."))])
    confirm_password = PasswordField(
        _l("Confirm password"),
        validators=[DataRequired(), EqualTo("password", message=_l("Passwords must match."))],
    )
    submit = SubmitField(_l("Create account"))


class LoginForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = SubmitField(_l("Keep me signed in"))  # rendered as a checkbox in the template
    submit = SubmitField(_l("Log in"))


class ForgotPasswordForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Send reset link"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("New password"), validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        _l("Confirm new password"),
        validators=[DataRequired(), EqualTo("password", message=_l("Passwords must match."))],
    )
    submit = SubmitField(_l("Reset password"))


class ListingForm(FlaskForm):
    game_name = StringField(_l("Game name"), validators=[DataRequired(), Length(max=150)])

    # Native <input type="date"> renders according to the visitor's OS/
    # browser locale (e.g. dd/mm/yyyy on a Portuguese Windows machine),
    # so it's kept as-is - it's both correct and avoids manual-entry
    # errors. <input type="time"> is less reliable across locales (some
    # show a 12-hour AM/PM picker), so that one stays as an explicit
    # 24-hour text field.
    game_date = DateField(_l("Date"), validators=[DataRequired()])
    game_time = TimeField(
        _l("Time"),
        format="%H:%M",
        widget=TextInput(),
        validators=[DataRequired()],
        render_kw={
            "placeholder": _l("HH:MM (24-hour)"),
            "inputmode": "numeric",
            "data-mask": "time",
        },
    )

    # "shop" = pick from the pre-defined Hobby Shop list, "free" = type your own.
    location_type = SelectField(
        _l("Location type"),
        choices=[ ("shop", _l("Hobby Shop - Listed below")), ("free", _l("Personalized location"))],
        validators=[DataRequired()],
    )
    shop_id = SelectField(_l("Hobby shop"), coerce=int, validators=[Optional()])
    free_location_text = StringField(_l("Location (address / description)"), validators=[Optional(), Length(max=255)])
    region = StringField(_l("Region"), validators=[Optional(), Length(max=100)])

    players_required = IntegerField(
        _l("Players required"), validators=[DataRequired(), NumberRange(min=1, max=100)], default=2
    )
    notes = TextAreaField(_l("Notes (optional)"), validators=[Optional(), Length(max=2000)])
    submit = SubmitField(_l("Publish listing"))


class EnrollForm(FlaskForm):
    notes = StringField(_l("Notes (e.g. faction / deck / character)"), validators=[Optional(), Length(max=255)])
    submit = SubmitField(_l("Join this game"))


class MessageForm(FlaskForm):
    body = TextAreaField(_l("Message"), validators=[DataRequired(), Length(max=4000)])
    submit = SubmitField(_l("Send"))


class HobbyShopForm(FlaskForm):
    name = StringField(_l("Shop name"), validators=[DataRequired(), Length(max=150)])
    region = StringField(_l("Region"), validators=[DataRequired(), Length(max=100)])
    address = StringField(_l("Address"), validators=[Optional(), Length(max=255)])
    active = SelectField(_l("Active"), choices=[("1", _l("Yes")), ("0", _l("No"))], default="1")
    submit = SubmitField(_l("Save shop"))


class MaintenanceBannerForm(FlaskForm):
    """
    Lets an admin schedule a site-wide notice (e.g. "DB update tonight
    22:00-23:00") that only shows up on the site during the chosen
    time window, then disappears automatically - no manual clean-up.
    """

    message = TextAreaField(
        _l("Banner message"),
        validators=[DataRequired(), Length(max=500)],
        render_kw={"placeholder": _l("e.g. Scheduled database maintenance tonight, the site may be briefly unavailable.")},
    )
    starts_at = DateTimeLocalField(
        _l("Starts at"), format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    ends_at = DateTimeLocalField(
        _l("Ends at"), format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    submit = SubmitField(_l("Publish banner"))

    def validate_ends_at(self, field):
        if self.starts_at.data and field.data and field.data <= self.starts_at.data:
            raise ValidationError(_l("End time must be after the start time."))