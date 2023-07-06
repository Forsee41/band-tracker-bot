from datetime import datetime

import pytest

from band_tracker.core.artist import Artist
from band_tracker.core.enums import EventSource
from band_tracker.core.event import Event
from band_tracker.ticketmaster.client import get_artist, get_event
from test_data.temp_const import ARTISTS, EVENTS


class TestClient:
    @pytest.mark.parametrize(
        "raw_artist, expected_artist",
        [
            (
                ARTISTS.get("_embedded").get("attractions")[0],
                Artist(
                    name="The Orb",
                    spotify_link="https://open.spotify.com/artist/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true",
                    tickets_link="https://www.ticketmaster.com/the-orb-tickets/artist/806748",
                    inst_link="http://www.instagram.com/theorblive",
                    youtube_link="https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg",
                    upcoming_events_amount=8,
                    _source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171RCf"}
                    },
                ),
            ),
            (
                ARTISTS.get("_embedded").get("attractions")[1],
                Artist(
                    name="Jeff Tain Watts",
                    spotify_link=None,
                    tickets_link="https://www.ticketmaster.com/jeff-tain-watts-tickets/artist/844673",
                    inst_link=None,
                    youtube_link=None,
                    upcoming_events_amount=6,
                    _source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171RCf"}
                    },
                ),
            ),
        ],
    )
    def test_get_artist(self, raw_artist: dict, expected_artist: Artist) -> None:
        assert get_artist(raw_artist) == expected_artist

    def test_get_event_1(self) -> None:
        raw_event = EVENTS.get("_embedded").get("events")[0]
        event = Event(
            title="Shania Twain: Queen Of Me Tour",
            date=datetime(2023, 7, 15),
            venue="Ruoff Music Center",
            ticket_url="https://concerts.livenation.com/shania-twain-queen-of-me-tour-noblesville-indiana-07-15-2023/event/05005D55DD6D454E",
            _source_specific_data={
                EventSource.ticketmaster_api: {"id": "vvG1fZ949qhf4C"}
            },
        )
        assert get_event(raw_event) == event


if __name__ == "__main__":
    pytest.main()
