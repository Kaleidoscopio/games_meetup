"""
models.py
---------
All database tables, defined as SQLAlchemy models. SQLite stores this
as a single .db file (see config.py) which is enough for a small
community app and costs nothing to host.
"""

import secrets
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """A registered player."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locale = db.Column(db.String(5), nullable=True)  # e.g. "pt", "es" - None = use browser/session default
    
    # Password-reset support: a random single-use token with an
    # expiry time. Cleared out again once used.
    reset_token = db.Column(db.String(64), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    # --- Relationships -----------------------------------------------------
    listings = db.relationship("Listing", back_populates="creator", lazy="dynamic",
                                foreign_keys="Listing.creator_id")
    enrollments = db.relationship("Enrollment", back_populates="user", lazy="dynamic")

    # --- Password helpers ----------------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # --- Password reset token helpers ---------------------------------------
    def generate_reset_token(self, expires_in_minutes: int = 30) -> str:
        """Create a fresh single-use token for the 'forgot password' flow."""
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expires = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        return token

    def verify_reset_token(self, token: str) -> bool:
        return (
            self.reset_token is not None
            and self.reset_token == token
            and self.reset_token_expires is not None
            and self.reset_token_expires > datetime.utcnow()
        )

    def clear_reset_token(self) -> None:
        self.reset_token = None
        self.reset_token_expires = None

    def __repr__(self):
        return f"<User {self.username}>"


class HobbyShop(db.Model):
    """
    A pre-defined physical location (game/hobby store) that listing
    creators can pick from instead of typing a free-text address.
    Managed by admins via the admin maintenance page.
    """

    __tablename__ = "hobby_shops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    region = db.Column(db.String(100), nullable=False, index=True)
    address = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    listings = db.relationship("Listing", back_populates="shop", lazy="dynamic")

    def __repr__(self):
        return f"<HobbyShop {self.name} ({self.region})>"


class Listing(db.Model):
    """A game session someone wants to organise."""

    __tablename__ = "listings"

    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"          # closed manually by the creator
    STATUS_AUTO_CLOSED = "auto_closed"  # closed automatically by the scheduler

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    game_name = db.Column(db.String(150), nullable=False)

    # Date/time the game is planned for.
    game_datetime = db.Column(db.DateTime, nullable=False, index=True)

    # --- Location ------------------------------------------------------------
    # Either a pre-defined hobby shop OR a free-text location is used,
    # never both. `location_type` tells the templates/logic which one
    # applies.
    location_type = db.Column(db.String(10), nullable=False, default="free")  # "shop" | "free"
    shop_id = db.Column(db.Integer, db.ForeignKey("hobby_shops.id"), nullable=True)
    free_location_text = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(100), nullable=True, index=True)

    players_required = db.Column(db.Integer, nullable=False, default=1)

    status = db.Column(db.String(15), nullable=False, default=STATUS_OPEN, index=True)

    notes = db.Column(db.Text, nullable=True)  # optional extra info from the organiser

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    # --- Relationships -----------------------------------------------------
    creator = db.relationship("User", back_populates="listings", foreign_keys=[creator_id])
    shop = db.relationship("HobbyShop", back_populates="listings")
    enrollments = db.relationship("Enrollment", back_populates="listing",
                                   cascade="all, delete-orphan", lazy="dynamic")

    def location_display(self) -> str:
        """Human readable location string for templates/emails."""
        if self.location_type == "shop" and self.shop is not None:
            return f"{self.shop.name} ({self.shop.region})"
        return self.free_location_text or "Location TBD"

    def spots_taken(self) -> int:
        return self.enrollments.count()

    def spots_left(self) -> int:
        return max(self.players_required - self.spots_taken(), 0)

    def is_full(self) -> bool:
        return self.spots_left() <= 0

    def is_open(self) -> bool:
        return self.status == Listing.STATUS_OPEN

    def __repr__(self):
        return f"<Listing {self.game_name} @ {self.game_datetime}>"


class Enrollment(db.Model):
    """A user signing up to play in a listing."""

    __tablename__ = "enrollments"
    __table_args__ = (
        db.UniqueConstraint("listing_id", "user_id", name="uq_listing_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Free-text note from the enrolling player, e.g. "Playing Orks" or
    # "Bringing my own board".
    notes = db.Column(db.String(255), nullable=True)

    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    listing = db.relationship("Listing", back_populates="enrollments")
    user = db.relationship("User", back_populates="enrollments")

    def __repr__(self):
        return f"<Enrollment user={self.user_id} listing={self.listing_id}>"


class MaintenanceBanner(db.Model):
    """
    A site-wide notice an admin schedules ahead of time (e.g. a
    database update or server restart). It only shows up on the site
    between `starts_at` and `ends_at` - no manual "turn it off"
    step needed once the window passes.
    """

    __tablename__ = "maintenance_banners"
    __table_args__ = {"sqlite_autoincrement": True}

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)

    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User")

    def is_active(self, at: datetime = None) -> bool:
        at = at or datetime.utcnow()
        return self.starts_at <= at <= self.ends_at

    def __repr__(self):
        return f"<MaintenanceBanner {self.starts_at}\u2013{self.ends_at}>"


class Message(db.Model):
    """A single direct message between two users, optionally linked to a listing."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Optional: which listing this conversation relates to, so the UI
    # can group messages by "game" as well as by conversation partner.
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True)

    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])
    listing = db.relationship("Listing")

    def __repr__(self):
        return f"<Message {self.sender_id} -> {self.recipient_id}>"