"""
blueprints/listings.py
-----------------------
Everything to do with game listings: creating them, browsing/filtering
them, enrolling as a player, and closing them (manually) once a game
is arranged.
"""

from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from flask_babel import _

from extensions import db
from models import Listing, HobbyShop, Enrollment
from forms import ListingForm, EnrollForm
from utils.email_utils import send_listing_closed_email, send_new_enrollment_email
from utils.ics_utils import build_listing_ics

listings_bp = Blueprint("listings", __name__, url_prefix="/listings")


def _populate_shop_choices(form):
    """Fill the shop dropdown with active hobby shops, grouped alphabetically."""
    shops = HobbyShop.query.filter_by(active=True).order_by(HobbyShop.region, HobbyShop.name).all()
    form.shop_id.choices = [(0, _l("-- select a shop --"))] + [(s.id, f"{s.name} ({s.region})") for s in shops]


@listings_bp.route("/")
@login_required
def browse():
    """Main listing feed, with simple filters for mobile-friendly browsing."""
    region = request.args.get("region", "").strip()
    game = request.args.get("game", "").strip()

    query = Listing.query.filter_by(status=Listing.STATUS_OPEN)
    if region:
        query = query.filter(Listing.region.ilike(f"%{region}%"))
    if game:
        query = query.filter(Listing.game_name.ilike(f"%{game}%"))

    listings = query.order_by(Listing.game_datetime.asc()).all()
    return render_template("listings/list.html", listings=listings, region=region, game=game)


@listings_bp.route("/mine")
@login_required
def my_listings():
    """Listings the current user created, plus ones they've joined."""
    created = Listing.query.filter_by(creator_id=current_user.id).order_by(Listing.game_datetime.desc()).all()
    # Creators are now auto-enrolled in their own listing (see create()),
    # so exclude self-created ones here to avoid a listing showing up in
    # both "created" and "joined" at once.
    joined_ids = [
        e.listing_id for e in current_user.enrollments
        if e.listing.creator_id != current_user.id
    ]
    joined = Listing.query.filter(Listing.id.in_(joined_ids)).order_by(Listing.game_datetime.desc()).all() if joined_ids else []
    return render_template("listings/my_listings.html", created=created, joined=joined)


@listings_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = ListingForm()
    _populate_shop_choices(form)

    if form.validate_on_submit():
        game_datetime = datetime.combine(form.game_date.data, form.game_time.data)

        if form.location_type.data == "shop":
            if not form.shop_id.data:
                flash(_("Please select a hobby shop, or switch to a free-text location."), "danger")
                return render_template("listings/create.html", form=form)
            shop = HobbyShop.query.get(form.shop_id.data)
            listing = Listing(
                game_name=form.game_name.data.strip(),
                game_datetime=game_datetime,
                location_type="shop",
                shop_id=shop.id,
                region=shop.region,
                players_required=form.players_required.data,
                notes=form.notes.data,
                creator_id=current_user.id,
            )
        else:
            listing = Listing(
                game_name=form.game_name.data.strip(),
                game_datetime=game_datetime,
                location_type="free",
                free_location_text=form.free_location_text.data.strip() if form.free_location_text.data else None,
                region=form.region.data.strip() if form.region.data else None,
                players_required=form.players_required.data,
                notes=form.notes.data,
                creator_id=current_user.id,
            )

        db.session.add(listing)

        # The organiser is one of the players they're asking for, so
        # they take up one of the spots straight away (e.g. "2 players
        # required" shows as 1/2, not 0/2, right after publishing).
        listing.enrollments.append(Enrollment(user_id=current_user.id, notes="Organiser"))

        db.session.commit()
        flash(_("Listing published!"), "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("listings/create.html", form=form)


@listings_bp.route("/<int:listing_id>")
@login_required
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    enroll_form = EnrollForm()
    already_enrolled = listing.enrollments.filter_by(user_id=current_user.id).first() is not None
    return render_template(
        "listings/detail.html",
        listing=listing,
        enroll_form=enroll_form,
        already_enrolled=already_enrolled,
    )


@listings_bp.route("/<int:listing_id>/enroll", methods=["POST"])
@login_required
def enroll(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if not listing.is_open():
        flash(_("This listing is no longer open."), "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if listing.creator_id == current_user.id:
        flash(_("You can't join your own listing."), "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if listing.is_full():
        flash(_("Sorry, this listing is already full."), "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if listing.enrollments.filter_by(user_id=current_user.id).first():
        flash(_("You're already enrolled in this listing."), "info")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    form = EnrollForm()
    enrollment = Enrollment(listing_id=listing.id, user_id=current_user.id, notes=form.notes.data)
    db.session.add(enrollment)
    db.session.commit()

    try:
        send_new_enrollment_email(listing, listing.creator.email, current_user.username)
    except Exception:
        pass  # never block the request just because email failed

    flash(_("You're in! The organiser has been notified."), "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@listings_bp.route("/<int:listing_id>/leave", methods=["POST"])
@login_required
def leave(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if listing.creator_id == current_user.id:
        flash(_("You're the organiser, so you can't leave your own listing - close it instead."), "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    enrollment = listing.enrollments.filter_by(user_id=current_user.id).first()
    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()
        flash(_("You've left this listing."), "info")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@listings_bp.route("/<int:listing_id>/close", methods=["POST"])
@login_required
def close(listing_id):
    """
    Organiser manually closes the listing once the game is arranged.
    Sends a confirmation email (with a .ics calendar attachment) to
    everyone involved.
    """
    listing = Listing.query.get_or_404(listing_id)
    if listing.creator_id != current_user.id and not current_user.is_admin:
        abort(403)

    if not listing.is_open():
        flash(_("This listing is already closed."), "info")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    listing.status = Listing.STATUS_CLOSED
    listing.closed_at = datetime.utcnow()
    db.session.commit()

    recipients = [listing.creator.email] + [e.user.email for e in listing.enrollments]
    recipients = list(dict.fromkeys(recipients))

    try:
        ics_bytes = build_listing_ics(listing)
        send_listing_closed_email(listing, recipients, ics_bytes, auto_closed=False)
    except Exception:
        pass

    flash(_("Listing closed and calendar invites sent to all players."), "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))