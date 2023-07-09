from datetime import datetime

import pytest
from pydantic import HttpUrl

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.enums import EventSource
from band_tracker.core.event_update import EventUpdate
from band_tracker.ticketmaster.client import get_artist, get_event
from test_data.temp_const import ARTISTS, EVENTS


class TestClient:
    @pytest.mark.parametrize(
        "raw_artist, expected_artist",
        [
            (
                ARTISTS.get("_embedded").get("attractions")[0],
                ArtistUpdate(
                    name="The Orb",
                    socials={
                        "spotify": HttpUrl(
                            "https://open.spotify.com/artist"
                            "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true"
                        ),
                        "instagram": HttpUrl("http://www.instagram.com/theorblive"),
                        "youtube": HttpUrl(
                            "https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg"
                        ),
                    },
                    aliases=[],
                    tickets_link=HttpUrl(
                        "https://www.ticketmaster.com/the-orb-tickets/artist/806748"
                    ),
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171RCf"}
                    },
                    genres=["Rock", "Pop"],
                    images=[
                        HttpUrl(
                            "https://s1.ticketm.net"
                            "/dam/a/5a1/d9a78cdb-a7ce-"
                            "4e40-861d-4ad1c6b355a1_264701_ARTIST_PAGE_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net"
                            "/dam/a/5a1/d9a78cdb-a7ce-4e4"
                            "0-861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/"
                            "a/5a1/d9a78cdb-a7ce-4e40-861"
                            "d-4ad1c6b355a1_264701_RETINA_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/"
                            "5a1/d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_264701_CUSTOM.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a1/d"
                            "9a78cdb-a7ce-4e40-861d-"
                            "4ad1c6b355a1_264701_RETINA_PORTRAIT_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a"
                            "1/d9a78cdb-a7ce-4e40-"
                            "861d-4ad1c6b355a1_264701_RETINA_PORTRAIT_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a/5a"
                            "1/d9a78cdb-a7ce-4e40-"
                            "861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/a"
                            "/5a1/d9a78cdb-a7ce-4e40"
                            "-861d-4ad1c6b355a1_264701_TABLET_LANDSCAPE_3_2.jpg"
                        ),
                        HttpUrl("https://s1.ticketm.net/dbimages/33384a.jpg"),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/"
                            "a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c"
                            "6b355a1_264701_RECOMENDATION_16_9.jpg"
                        ),
                    ],
                ),
            ),
            (
                ARTISTS.get("_embedded").get("attractions")[1],
                ArtistUpdate(
                    name="Jeff Tain Watts",
                    tickets_link=HttpUrl(
                        "https://www.ticketmaster.com/"
                        "jeff-tain-watts-tickets/artist/844673"
                    ),
                    socials={"spotify": None, "youtube": None, "instagram": None},
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171OI0"}
                    },
                    aliases=[],
                    genres=["Jazz", "Jazz"],
                    images=[
                        HttpUrl(
                            "https://s1.ticketm.net/dam/"
                            "c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_TABLET_"
                            "LANDSCAPE_LARGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam"
                            "/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_1058"
                            "01_RETINA_PORTRAIT_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/"
                            "c/bea/03d47f66-d37b-4aca-"
                            "aa17-0135be64dbea_105801_RECOMENDATIO"
                            "N_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c/b"
                            "ea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RETINA_L"
                            "ANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam/c"
                            "/bea/03d47f66-d37b-4aca-aa17"
                            "-0135be64dbea_105801_CUSTOM.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/d"
                            "am/c/bea/03d47f66-d37b-4aca-"
                            "aa17-0135be64dbea_105801_EVENT_DETAI"
                            "L_PAGE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net"
                            "/dam/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_TA"
                            "BLET_LANDSCAPE_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/d"
                            "am/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_ARTI"
                            "ST_PAGE_3_2.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/dam"
                            "/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_RETI"
                            "NA_PORTRAIT_16_9.jpg"
                        ),
                        HttpUrl(
                            "https://s1.ticketm.net/d"
                            "am/c/bea/03d47f66-d37b-4aca-aa17-0135be64dbea_105801_"
                            "TABLET_LANDSCAPE_3_2.jpg"
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_get_artist(self, raw_artist: dict, expected_artist: ArtistUpdate) -> None:
        assert get_artist(raw_artist) == expected_artist

    def test_get_event_1(self) -> None:
        raw_event = EVENTS.get("_embedded").get("events")[0]
        event = EventUpdate(
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
            venue_city="Noblesville",
            venue_country="United States Of America",
            artists=[],
        )
        assert get_event(raw_event) == event


if __name__ == "__main__":
    pytest.main()
