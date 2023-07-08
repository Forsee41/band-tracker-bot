import logging
from datetime import datetime

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.core.event import Event

log = logging.getLogger(__name__)


def get_artist(raw_artist: dict) -> Artist:
    log.debug("get_artist invoke")

    def link_helper() -> dict | None:
        """helper function providing links for specified resources or None if there is no external Links found
        :return: dict with links or None if not found
        """
        external_links = raw_artist.get("externalLinks")
        if external_links is not None:
            links = {}
            for i in {"inst_link", "youtube_link", "spotify_link"}:
                links.update({i: external_links.get(i)[0]["url"]})
            return links
        return None

    modified_artist = {
        "name": raw_artist.get("name"),
        "socials": link_helper(),
        "tickets_link": raw_artist.get("url"),
        "source_specific_data": {
            EventSource.ticketmaster_api: {"id": raw_artist.get("id")}
        },
        "images": [image.get("url") for image in raw_artist.get("images", [])],
    }
    return Artist.model_validate(modified_artist)


def get_event(raw_event: dict) -> Event:
    log.debug("get_event invoke")

    def datetime_helper() -> datetime | None:
        format_string = "%Y-%m-%d"
        date = raw_event.get("dates", {}).get("start", {}).get("localDate")
        return datetime.strptime(date, format_string) if date else None

    modified_event = {
        "title": raw_event.get("name"),
        "date": datetime_helper(),
        "venue": raw_event.get("_embedded", {})
        .get("venues", {})[0]
        .get(
            "name",
        ),
        "ticket_url": raw_event.get("url"),
        "source_specific_data": {
            EventSource.ticketmaster_api: {"id": raw_event.get("id")}
        },
    }
    return Event.model_validate(modified_event)
