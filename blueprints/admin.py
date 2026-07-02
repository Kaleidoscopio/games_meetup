"""
blueprints/admin.py
--------------------
Admin-only pages for simple database maintenance:
  - manage the Hobby Shop list (add / edit / deactivate)
  - view & delete users
  - view & force-close / delete listings
No fancy admin framework is used - just a few plain, guarded routes,
which keeps the app light and cheap to run.
"""

from functools import wraps
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from flask_babel import _

from extensions import db
from models import User, HobbyShop, Listing, Message
from forms import HobbyShopForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_func):
    """Decorator that limits a route to logged-in admins only."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "listings_open": Listing.query.filter_by(status=Listing.STATUS_OPEN).count(),
        "listings_closed": Listing.query.filter(Listing.status != Listing.STATUS_OPEN).count(),
        "shops": HobbyShop.query.count(),
        "messages": Message.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# --- Hobby shop maintenance --------------------------------------------------

@admin_bp.route("/shops", methods=["GET", "POST"])
@login_required
@admin_required
def shops():
    form = HobbyShopForm()
    if form.validate_on_submit():
        shop = HobbyShop(
            name=form.name.data.strip(),
            region=form.region.data.strip(),
            address=form.address.data.strip() if form.address.data else None,
            active=(form.active.data == "1"),
        )
        db.session.add(shop)
        db.session.commit()
        flash(_("Hobby shop added."), "success")
        return redirect(url_for("admin.shops"))

    all_shops = HobbyShop.query.order_by(HobbyShop.region, HobbyShop.name).all()
    return render_template("admin/shops.html", form=form, shops=all_shops)


@admin_bp.route("/shops/<int:shop_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_shop(shop_id):
    shop = HobbyShop.query.get_or_404(shop_id)
    shop.active = not shop.active
    db.session.commit()
    flash(_("{shop.name} is now {'active' if shop.active else 'inactive'}."), "info")
    return redirect(url_for("admin.shops"))


@admin_bp.route("/shops/<int:shop_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_shop(shop_id):
    shop = HobbyShop.query.get_or_404(shop_id)
    if shop.listings.count() > 0:
        flash(_("Can't delete a shop that has listings - deactivate it instead."), "danger")
    else:
        db.session.delete(shop)
        db.session.commit()
        flash(_("Hobby shop deleted."), "info")
    return redirect(url_for("admin.shops"))


# --- User maintenance ---------------------------------------------------------

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash(_("You can't change your own admin status."), "warning")
        return redirect(url_for("admin.users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(_("{user.username} admin status: {user.is_admin}."), "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash(_("You can't delete your own account from here."), "warning")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(_("User deleted."), "info")
    return redirect(url_for("admin.users"))


# --- Listing maintenance -------------------------------------------------------

@admin_bp.route("/listings")
@login_required
@admin_required
def listings():
    all_listings = Listing.query.order_by(Listing.created_at.desc()).all()
    return render_template("admin/listings.html", listings=all_listings)


@admin_bp.route("/listings/<int:listing_id>/force-close", methods=["POST"])
@login_required
@admin_required
def force_close(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = Listing.STATUS_CLOSED
    listing.closed_at = datetime.utcnow()
    db.session.commit()
    flash(_("Listing force-closed."), "info")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash(_("Listing deleted."), "info")
    return redirect(url_for("admin.listings"))
