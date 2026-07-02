"""
utils/email_utils.py
---------------------
Small wrapper around Flask-Mail so the rest of the app can send
emails with one function call. If no SMTP credentials are configured
(local development), the email is printed to the console instead of
raising an error - this keeps the app fully runnable with zero setup.
"""

from flask import current_app, render_template
from flask_mail import Message as MailMessage
from flask_babel import lazy_gettext as _l

from extensions import mail


def send_email(subject: str, recipients: list[str], html_body: str, attachments: list[tuple] | None = None) -> None:
    """
    Send an HTML email.

    attachments: optional list of (filename, mimetype, data) tuples,
    used for attaching .ics calendar invites.
    """
    if not recipients:
        return

    # No mail server configured -> just log it, don't crash the app.
    if not current_app.config.get("MAIL_USERNAME") and not current_app.config.get("MAIL_SUPPRESS_SEND"):
        print(f"\n----- [DEV MODE] Would send email -----\nTo: {recipients}\nSubject: {subject}\n{html_body}\n----------------------------------------\n")
        return

    msg = MailMessage(subject=subject, recipients=recipients, html=html_body)

    if attachments:
        for filename, mimetype, data in attachments:
            msg.attach(filename, mimetype, data)

    try:
        mail.send(msg)
    except Exception as exc:  # pragma: no cover - defensive, don't crash user requests
        current_app.logger.error(_l(f"Failed to send email to {recipients}: {exc}"))


def send_password_reset_email(user, reset_url: str) -> None:
    html = render_template("email/reset_password.html", user=user, reset_url=reset_url)
    send_email(_l("Reset your Games Meetup password"), [user.email], html)


def send_listing_closed_email(listing, recipients: list[str], ics_bytes: bytes, auto_closed: bool) -> None:
    html = render_template("email/listing_closed.html", listing=listing, auto_closed=auto_closed)
    subject = _l(f"Your game '{listing.game_name}' is confirmed") if not auto_closed else \
        _l(f"Listing '{listing.game_name}' was automatically closed")
    send_email(
        subject,
        recipients,
        html,
        attachments=[("game_invite.ics", "text/calendar", ics_bytes)] if ics_bytes else None,
    )


def send_new_enrollment_email(listing, organiser_email: str, player_username: str) -> None:
    html = render_template("email/new_enrollment.html", listing=listing, player_username=player_username)
    send_email(_l(f"New player joined '{listing.game_name}'"), [organiser_email], html)


def send_new_message_email(recipient, sender, listing=None) -> None:
    html = render_template("email/new_message.html", recipient=recipient, sender=sender, listing=listing)
    send_email(_l(f"New message from {sender.username} on Games Meetup"), [recipient.email], html)
