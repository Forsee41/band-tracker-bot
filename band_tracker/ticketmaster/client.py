import logging
from datetime import datetime

from band_tracker.config.log import load_log_config
from band_tracker.core.artist import Artist
from band_tracker.core.event import Event

load_log_config()
log = logging.getLogger(__name__)


def link_helper(d: dict, resource: str) -> str | None:
    external_links = d.get("externalLinks")
    if external_links is not None and resource in external_links:
        return external_links.get(resource)[0]["url"]
    return None


def get_artist(raw_artist: dict) -> Artist:
    log.info("get_artist invoke")

    modified_artist = {
        "id": raw_artist.get("id"),
        "name": raw_artist.get("name"),
        "spotify_link": link_helper(raw_artist, "spotify"),
        "tickets_link": raw_artist.get("url"),
        "inst_link": link_helper(raw_artist, "instagram"),
        "youtube_link": link_helper(raw_artist, "youtube"),
        "upcoming_events_amount": raw_artist.get("upcomingEvents").get("_total"),
        "_source_specific_data": None,
    }
    return Artist(**modified_artist)


def get_event(raw_event: dict) -> Event:
    log.info("get_event invoke")

    format_string = "%Y-%m-%d"
    modified_event = {
        "id": raw_event.get("id"),
        "title": raw_event.get("name"),
        "date": datetime.strptime(
            raw_event.get("dates").get("start").get("localDate"), format_string
        ),
        "venue": raw_event.get("_embedded").get("venues")[0].get("name"),
        "ticket_url": raw_event.get("url"),
    }
    return Event(**modified_event)
