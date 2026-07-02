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
from flask_babel import gettext as _ 
from threading import Thread
from extensions import mail

#   Helpers for sending emails asynchronously in a background thread.
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            # Move the error logger here since the thread executes independently
            app.logger.error(f"Failed to send async email to {msg.recipients}: {exc}")


def send_email(subject: str, recipients: list[str], html_body: str, attachments: list[tuple] | None = None) -> None:
    """
    Send an HTML email asynchronously.

    attachments: optional list of (filename, mimetype, data) tuples,
    used for attaching .ics calendar invites.
    """
    if not recipients:
        return

    # If MAIL_SUPPRESS_SEND is True, or if no SMTP server is configured, print the email to the console instead of sending it.
    if current_app.config.get("MAIL_SUPPRESS_SEND") or (not current_app.config.get("MAIL_SERVER") and not current_app.config.get("MAIL_USERNAME")):
        print(f"\n----- [DEV MODE] Would send email -----\nTo: {recipients}\nSubject: {subject}\n{html_body}\n----------------------------------------\n")
        return

    msg = MailMessage(subject=subject, recipients=recipients, html=html_body)

    if attachments:
        for filename, mimetype, data in attachments:
            msg.attach(filename, mimetype, data)

    # 1. Fetch the real application instance out of the current_app proxy wrapper
    app = current_app._get_current_object()

    # 2. Spawn and start the background thread, passing the app instance and message payload
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user, reset_url: str) -> None:
    html = render_template("email/reset_password.html", user=user, reset_url=reset_url)
    send_email(_("Reset your Games Meetup password"), [user.email], html)


def send_listing_closed_email(listing, recipients: list[str], ics_bytes: bytes, auto_closed: bool) -> None:
    html = render_template("email/listing_closed.html", listing=listing, auto_closed=auto_closed)
    
    if not auto_closed:
        #  .format() after gettext to allow for pybabel extraction of the string for translation, 
        # while still allowing for dynamic game name insertion.
        subject = _("Your game '{game_name}' is confirmed").format(game_name=listing.game_name)
    else:
        subject = _("Listing '{game_name}' was automatically closed").format(game_name=listing.game_name)
        
    send_email(
        subject,
        recipients,
        html,
        attachments=[("game_invite.ics", "text/calendar", ics_bytes)] if ics_bytes else None,
    )


def send_new_enrollment_email(listing, organiser_email: str, player_username: str) -> None:
    html = render_template("email/new_enrollment.html", listing=listing, player_username=player_username)
    subject = _("New player joined '{game_name}'").format(game_name=listing.game_name)
    send_email(subject, [organiser_email], html)


def send_new_message_email(recipient, sender, listing=None) -> None:
    html = render_template("email/new_message.html", recipient=recipient, sender=sender, listing=listing)
    subject = _("New message from {username} on Games Meetup").format(username=sender.username)
    send_email(subject, [recipient.email], html)