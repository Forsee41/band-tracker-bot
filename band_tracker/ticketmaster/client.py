import logging
from datetime import datetime

from pydantic import BaseModel

from band_tracker.core.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.core.enums import EventSource
from band_tracker.core.errors import DeserializationError
from band_tracker.core.event_update import EventUpdate

log = logging.getLogger(__name__)


class JSONData(BaseModel):
    _embedded: dict[str, list]
    page: dict[str, dict]


def get_artist(raw_artist: dict) -> ArtistUpdate:
    log.debug("get_artist invoke")

    def artist_socials_helper() -> ArtistUpdateSocials:
        """helper function providing links for specified resources or
            None if there is no external Links found
        :return: dict with links or None if not found
        """
        external_links = raw_artist.get("externalLinks")
        if external_links is not None:
            links = {}
            for i in {"instagram", "youtube", "spotify"}:
                if external_links.get(i) is not None:
                    links.update({i: external_links.get(i)[0]["url"]})
                else:
                    links.update({i: None})
            return ArtistUpdateSocials(**links)
        return ArtistUpdateSocials(spotify=None, youtube=None, instagram=None)

    def genres_helper() -> list:
        classifications = raw_artist.get("classifications")
        if classifications:
            music_classifications = [
                classification
                for classification in classifications
                if classification.get("segment", {}).get("name") == "Music"
            ]
            if music_classifications:
                genres = [
                    [
                        classification.get("genre", {}).get("name"),
                        classification.get("subGenre", {}).get("name"),
                    ]
                    for classification in music_classifications
                ]
                if genres:
                    return [genre for genre in genres[0] if genre is not None]
        return []

    modified_artist = {
        "name": raw_artist.get("name"),
        "socials": artist_socials_helper(),
        "tickets_link": raw_artist.get("url"),
        "source_specific_data": {
            EventSource.ticketmaster_api: {"id": raw_artist.get("id")}
        },
        "images": [image.get("url") for image in raw_artist.get("images", [])],
        "genres": genres_helper(),
        "aliases": raw_artist.get("aliases", []),
    }
    return ArtistUpdate.model_validate(modified_artist)


def get_event(raw_event: dict) -> EventUpdate:
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
        "venue_city": raw_event.get("_embedded", {})
        .get("venues", {})[0]
        .get("city", {})
        .get("name"),
        "venue_country": raw_event.get("_embedded", {})
        .get("venues", {})[0]
        .get("country", {})
        .get("name"),
    }
    return EventUpdate.model_validate(modified_event)


def get_all_artists(raw_dict: dict[str, dict]) -> list[ArtistUpdate]:
    try:
        json_data = JSONData.model_validate(raw_dict)
        artists = json_data._embedded["attractions"]
    except ValueError:
        raise DeserializationError("invalid json", EventSource.ticketmaster_api)
    output = []
    for i in artists:
        output.append(get_artist(i))
    return output


def get_all_events(raw_dict: dict[str, dict]) -> list[EventUpdate]:
    try:
        json_data = JSONData.model_validate(raw_dict)
        events = json_data._embedded["events"]
    except ValueError:
        raise DeserializationError("invalid json", EventSource.ticketmaster_api)
    output = []
    for i in events:
        output.append(get_event(i))
    return output
