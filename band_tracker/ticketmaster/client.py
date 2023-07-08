import logging
from datetime import datetime

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.core.errors import DeserializationError
from band_tracker.core.event import Event

log = logging.getLogger(__name__)


def _get_artist_event_amount(raw_artist: dict) -> int:
    try:
        upcoming_events: dict = raw_artist["upcomingEvents"]
    except KeyError:
        raise DeserializationError(
            "Raw artist doesn't have an upcomingEvents field",
            api=EventSource.ticketmaster_api,
        )
    try:
        total_events_amount = upcoming_events["_total"]
    except KeyError:
        raise DeserializationError(
            "upcomingEvents field of raw artist doesn't have a _total field",
            api=EventSource.ticketmaster_api,
        )
    try:
        total_events_amount_int = int(total_events_amount)
    except ValueError:
        raise DeserializationError(
            "total upcoming events value cannot be casted to int",
            api=EventSource.ticketmaster_api,
        )
    return total_events_amount_int


def get_artist(raw_artist: dict) -> Artist:
    log.debug("get_artist invoke")

    def link_helper(resource: str) -> str | None:
        """helper function providing a link for a given resource or None if not found
        :param resource: resource name ("instagram", "spotify", etc.)
        :return: link or None if not found
        """
        external_links = raw_artist.get("externalLinks")
        if external_links is not None and resource in external_links:
            return external_links.get(resource)[0]["url"]
        return None

    events_amount = _get_artist_event_amount(raw_artist=raw_artist)

    modified_artist = {
        "name": raw_artist.get("name"),
        "spotify_link": link_helper("spotify"),
        "tickets_link": raw_artist.get("url"),
        "inst_link": link_helper("instagram"),
        "youtube_link": link_helper("youtube"),
        "upcoming_events_amount": events_amount,
        "source_specific_data": {
            EventSource.ticketmaster_api: {"id": raw_artist.get("id")}
        },
    }
    return Artist(**modified_artist)


def get_event(raw_event: dict) -> Event:
    log.debug("get_event invoke")

    format_string = "%Y-%m-%d"
    modified_event = {
        "title": raw_event.get("name"),
        "date": datetime.strptime(
            raw_event.get("dates").get("start").get("localDate"),  # type: ignore TODO
            format_string,
        ),
        "venue": raw_event.get("_embedded")
        .get("venues")[0]  # type: ignore TODO
        .get("name"),
        "ticket_url": raw_event.get("url"),
        "source_specific_data": {
            EventSource.ticketmaster_api: {"id": raw_event.get("id")}
        },
    }
    return Event(**modified_event)
