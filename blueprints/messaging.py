"""
blueprints/messaging.py
------------------------
Simple direct-messaging between two users so they can arrange the
details of a game (exact time, faction, who brings what, etc).
Conversations are identified by the pair of users involved, and can
optionally be tied to a specific listing for context.
"""

from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from extensions import db
from models import Message, User, Listing
from forms import MessageForm
from utils.email_utils import send_new_message_email

messaging_bp = Blueprint("messaging", __name__, url_prefix="/messages")


@messaging_bp.route("/")
@login_required
def inbox():
    """
    List conversations: one row per "other user" the current user has
    exchanged messages with, showing the most recent message.
    """
    all_messages = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).order_by(Message.sent_at.desc()).all()

    conversations = {}
    for m in all_messages:
        other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in conversations:
            conversations[other_id] = m  # first hit is the most recent, thanks to ordering

    other_users = {u.id: u for u in User.query.filter(User.id.in_(conversations.keys())).all()} if conversations else {}

    return render_template("messaging/inbox.html", conversations=conversations, other_users=other_users)


@messaging_bp.route("/with/<int:user_id>", methods=["GET", "POST"])
@login_required
def thread(user_id):
    other_user = User.query.get_or_404(user_id)
    if other_user.id == current_user.id:
        abort(400)

    listing_id = request.args.get("listing_id", type=int)
    listing = Listing.query.get(listing_id) if listing_id else None

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            recipient_id=other_user.id,
            listing_id=listing.id if listing else None,
            body=form.body.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()

        try:
            send_new_message_email(other_user, current_user, listing)
        except Exception:
            pass

        return redirect(url_for("messaging.thread", user_id=other_user.id, listing_id=listing_id))

    # Mark incoming messages from this user as read.
    unread = Message.query.filter_by(sender_id=other_user.id, recipient_id=current_user.id, read_at=None).all()
    if unread:
        from datetime import datetime
        for m in unread:
            m.read_at = datetime.utcnow()
        db.session.commit()

    thread_messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == other_user.id),
            and_(Message.sender_id == other_user.id, Message.recipient_id == current_user.id),
        )
    ).order_by(Message.sent_at.asc()).all()

    return render_template(
        "messaging/thread.html", other_user=other_user, messages=thread_messages, form=form, listing=listing
    )
