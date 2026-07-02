"""
utils/ics_utils.py
-------------------
Generates a standard .ics calendar file for a confirmed listing so
players can add the game to Google Calendar / Outlook / Apple
Calendar with one tap. This is a free, open standard - no paid
calendar API (e.g. Google Calendar API quota) is required.
"""

from datetime import timedelta
from ics import Calendar, Event


def build_listing_ics(listing) -> bytes:
    """Return the raw bytes of an .ics file for the given Listing."""
    cal = Calendar()
    event = Event()
    event.name = f"Games Meetup: {listing.game_name}"
    event.begin = listing.game_datetime
    # Default to a 2-hour block if we don't know the real duration.
    event.end = listing.game_datetime + timedelta(hours=2)
    event.location = listing.location_display()
    event.description = (
        f"Organised via Games Meetup by {listing.creator.username}.\n"
        f"Players required: {listing.players_required}\n"
        + (f"Notes: {listing.notes}" if listing.notes else "")
    )
    cal.events.add(event)
    return str(cal).encode("utf-8")
