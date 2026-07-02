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
from flask_babel import _

def build_listing_ics(listing) -> bytes:
    """Return the raw bytes of an .ics file for the given Listing."""
    cal = Calendar()
    event = Event()
    event.name = f"Games Meetup: {listing.game_name}"
    event.begin = listing.game_datetime
    # Default to a 2-hour block if we don't know the real duration.
    event.end = listing.game_datetime + timedelta(hours=2)
    event.location = listing.location_display()

# Build description components using translated templates
    desc_lines = [
        _("Organised via Games Meetup by %(username)s.", username=listing.creator.username),
        _("Players required: %(count)s", count=listing.players_required)
    ]
    
    if listing.notes:
        desc_lines.append(_("Notes: %(notes)s", notes=listing.notes))
        
    event.description = "\n".join(desc_lines)
    cal.events.add(event)
    return str(cal).encode("utf-8")
