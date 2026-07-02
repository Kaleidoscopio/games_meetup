"""
utils/scheduler.py
-------------------
Runs an in-process background job (APScheduler) that periodically
looks for listings whose game date is more than AUTO_CLOSE_AFTER_DAYS
days in the past and are still marked "open", then closes them and
notifies everyone involved. Running the scheduler inside the same
process as the web app avoids paying for a separate cron/worker
service, keeping hosting costs at zero.
"""

from datetime import datetime, timedelta

from extensions import db, scheduler
from models import Listing
from utils.email_utils import send_listing_closed_email
from utils.ics_utils import build_listing_ics


def auto_close_expired_listings(app):
    """
    Close any listing whose game date + AUTO_CLOSE_AFTER_DAYS has
    passed and that is still open. Runs inside an app context because
    it needs DB + mail access but is triggered outside a normal
    request.
    """
    with app.app_context():
        cutoff_days = app.config["AUTO_CLOSE_AFTER_DAYS"]
        now = datetime.utcnow()

        stale_listings = Listing.query.filter(
            Listing.status == Listing.STATUS_OPEN,
            Listing.game_datetime <= now - timedelta(days=cutoff_days),
        ).all()

        for listing in stale_listings:
            listing.status = Listing.STATUS_AUTO_CLOSED
            listing.closed_at = now
            db.session.add(listing)

            recipients = [listing.creator.email] + [e.user.email for e in listing.enrollments]
            recipients = list(dict.fromkeys(recipients))  # de-duplicate, keep order

            try:
                ics_bytes = build_listing_ics(listing)
                send_listing_closed_email(listing, recipients, ics_bytes, auto_closed=True)
            except Exception as exc:  # pragma: no cover - never let notification errors block closing
                app.logger.error(f"Failed to notify listing {listing.id} auto-close: {exc}")

        if stale_listings:
            db.session.commit()
            app.logger.info(f"Auto-closed {len(stale_listings)} expired listing(s).")


def init_scheduler(app):
    """Register and start the recurring job. Called once from app.py."""
    interval = app.config["SCHEDULER_INTERVAL_MINUTES"]

    # avoid double-registration when Flask's reloader spawns two processes
    if not scheduler.get_jobs():
        scheduler.add_job(
            func=lambda: auto_close_expired_listings(app),
            trigger="interval",
            minutes=interval,
            id="auto_close_listings",
            replace_existing=True,
            next_run_time=datetime.utcnow() + timedelta(seconds=10),  # run once shortly after startup
        )
    if not scheduler.running:
        scheduler.start()
