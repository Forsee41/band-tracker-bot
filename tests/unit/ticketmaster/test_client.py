from datetime import datetime

import pytest
from pydantic import HttpUrl

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
                    socials={
                        "spotify_link": HttpUrl(
                            "https://open.spotify.com/artist"
                            "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true"
                        ),
                        "inst_link": HttpUrl("http://www.instagram.com/theorblive"),
                        "youtube_link": HttpUrl(
                            "https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg"
                        ),
                    },
                    tickets_link=HttpUrl(
                        "https://www.ticketmaster.com/the-orb-tickets/artist/806748"
                    ),
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171RCf"}
                    },
                    images=[
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_ARTIST_PAGE_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_RETINA_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_CUSTOM.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_RETINA_PORTRAIT_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_RETINA_PORTRAIT_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_3_2.jpg"
                        ),
                        HttpUrl("https://s1.ticketm.net/dbimages/33384a.jpg"),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_RECOMENDATION_16_9.jpg"
                        ),
                    ],
                ),
            ),
            (
                ARTISTS.get("_embedded").get("attractions")[1],
                Artist(
                    name="Jeff Tain Watts",
                    tickets_link=HttpUrl(
                        "https://www.ticketmaster.com/"
                        "jeff-tain-watts-tickets/artist/844673"
                    ),
                    socials={},
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171OI0"}
                    },
                    images=[
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RETINA_PORTRAIT_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RECOMENDATION_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RETINA_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_CUSTOM.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_EVENT_DETAIL_PAGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_TABLET_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_ARTIST_PAGE_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RETINA_PORTRAIT_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_TABLET_LANDSCAPE_3_2.jpg"
                        ),
                    ],
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
            ticket_url=HttpUrl(
                "https://concerts.livenation.com/shania-twain-queen-of-me-tour-"
                "noblesville-indiana-07-15-2023/event/05005D55DD6D454E"
            ),
            source_specific_data={
                EventSource.ticketmaster_api: {"id": "vvG1fZ949qhf4C"}
            },
        )
        assert get_event(raw_event) == event


if __name__ == "__main__":
    pytest.main()
