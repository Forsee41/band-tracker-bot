from datetime import datetime

import pytest
from pydantic import HttpUrl

from band_tracker.core.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.core.enums import EventSource
from band_tracker.core.event_update import EventUpdate, EventUpdateSales
from band_tracker.ticketmaster.client import (
    get_all_artists,
    get_all_events,
    get_artist,
    get_event,
)
from test_data.temp_const import ARTISTS, ARTISTS_SMALL, EVENTS, EVENTS_SMALL


class TestClient:
    @pytest.mark.parametrize(
        "raw_artist, expected_artist",
        [
            (
                ARTISTS.get("_embedded").get("attractions")[0],
                ArtistUpdate(
                    name="The Orb",
                    socials=ArtistUpdateSocials(
                        spotify=HttpUrl(
                            "https://open.spotify.com/artist"
                            "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true"
                        ),
                        instagram=HttpUrl("http://www.instagram.com/theorblive"),
                        youtube=HttpUrl(
                            "https://www.youtube.com/channel/UCpoyFBLTLfbT2Z1D1AnlvLg"
                        ),
                    ),
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
                    socials=ArtistUpdateSocials(
                        **{"spotify": None, "youtube": None, "instagram": None}
                    ),
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
            artists=["K8vZ91719n0", "K8vZ917_bOf"],
            images=[
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47"
                    "cc9b10-4904-4dec-b1d6-539e44a521d1_1825531_RETINA_PORTRAIT_3_2.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_EVENT_DETAIL_PAGE_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904"
                    "-4dec-b1d6-539e44a521d1_1825531_RETINA_LANDSCAPE_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_TABLET_LANDSCAPE_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_RECOMENDATION_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_TABLET_LANDSCAPE_3_2.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904"
                    "-4dec-b1d6-539e44a521d1_1825531_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_CUSTOM.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_RETINA_PORTRAIT_16_9.jpg"
                ),
                HttpUrl(
                    "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                    "4dec-b1d6-539e44a521d1_1825531_ARTIST_PAGE_3_2.jpg"
                ),
            ],
            sales=EventUpdateSales(
                on_sale=True, price_max=249.95, price_min=39.95, currency="USD"
            ),
        )
        assert get_event(raw_event) == event

    def test_get_all_artists(self) -> None:
        artists_list = [
            ArtistUpdate(
                name="Solina Cello-Ensemble",
                socials=ArtistUpdateSocials(
                    spotify=None,
                    instagram=None,
                    youtube=None,
                ),
                aliases=[],
                tickets_link=HttpUrl(
                    "https://www.ticketmaster.com/solina"
                    "-celloensemble-tickets/artist/2772347"
                ),
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "K8vZ917_Fi7"}
                },
                genres=["Classical", "Classical/Vocal"],
                images=[
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c"
                        "-4f7e-a7aa-1932aab77518_105461_TABLET_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479"
                        "c-4f7e-a7aa-1932aab77518_105461_RETINA_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e-a7aa"
                        "-1932aab77518_105461_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e-a"
                        "7aa-1932aab77518_105461_RETINA_PORTRAIT_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_RETINA_PORTRAIT_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_TABLET_LANDSCAPE_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_EVENT_DETAIL_PAGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_CUSTOM.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_RECOMENDATION_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                        "-a7aa-1932aab77518_105461_ARTIST_PAGE_3_2.jpg"
                    ),
                ],
            ),
            ArtistUpdate(
                name="Maze featuring Frankie Beverly",
                socials=ArtistUpdateSocials(
                    spotify=None,
                    instagram=None,
                    youtube=None,
                ),
                aliases=["frankie beverly and maze", "maze frankie beverly"],
                tickets_link=HttpUrl(
                    "https://www.ticketmaster.com/maze-f"
                    "eaturing-frankie-beverly-tickets/artist/735607"
                ),
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "K8vZ9171Idf"}
                },
                genres=["R&B", "Soul"],
                images=[
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-"
                        "b884-4406b8ab64cd_1600911_TABLET_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-"
                        "b884-4406b8ab64cd_1600911_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-b"
                        "884-4406b8ab64cd_1600911_RETINA_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-b"
                        "884-4406b8ab64cd_1600911_RETINA_PORTRAIT_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-b"
                        "884-4406b8ab64cd_1600911_RECOMENDATION_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff"
                        "0-b884-4406b8ab64cd_1600911_CUSTOM.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4f"
                        "f0-b884-4406b8ab64cd_1600911_EVENT_DETAIL_PAGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-"
                        "b884-4406b8ab64cd_1600911_ARTIST_PAGE_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0"
                        "-b884-4406b8ab64cd_1600911_RETINA_PORTRAIT_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0"
                        "-b884-4406b8ab64cd_1600911_TABLET_LANDSCAPE_3_2.jpg"
                    ),
                ],
            ),
        ]
        assert get_all_artists(ARTISTS_SMALL) == artists_list

    def test_get_all_events(self) -> None:
        events_list = [
            EventUpdate(
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
                artists=["K8vZ91719n0", "K8vZ917_bOf"],
                images=[
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47"
                        "cc9b10-4904-4dec-b1d6-539e44a521"
                        "d1_1825531_RETINA_PORTRAIT_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_EVENT_DETAIL_PAGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904"
                        "-4dec-b1d6-539e44a521d1_1825531_RETINA_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_TABLET_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_RECOMENDATION_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_TABLET_LANDSCAPE_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904"
                        "-4dec-b1d6-539e44a521d1_182553"
                        "1_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_CUSTOM.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_RETINA_PORTRAIT_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
                        "4dec-b1d6-539e44a521d1_1825531_ARTIST_PAGE_3_2.jpg"
                    ),
                ],
                sales=EventUpdateSales(
                    on_sale=True, price_max=249.95, price_min=39.95, currency="USD"
                ),
            ),
            EventUpdate(
                title="Imagine Dragons",
                date=datetime(2023, 7, 8),
                venue="American Family Insurance Amphitheater - Summerfest Grounds",
                ticket_url=HttpUrl(
                    "https://www.ticketmaster.com/imagine-dragon"
                    "s-milwaukee-wisconsin-07-08-20"
                    "23/event/07005D689BED1C00"
                ),
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "vvG1jZ9pxhDoYZ"}
                },
                venue_city="Milwaukee",
                venue_country="United States Of America",
                artists=["K8vZ917GSz7"],
                images=[
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_RECOMENDATION_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-"
                        "4afe-84f9-15560d797c90_1652911_ARTIST_PAGE_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_RETINA_PORTRAIT_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_RETINA_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_TABLET_LANDSCAPE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_TABLET_LANDSCAPE_LARGE_16_9.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4af"
                        "e-84f9-15560d797c90_1652911_TABLET_LANDSCAPE_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_RETINA_PORTRAIT_3_2.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_CUSTOM.jpg"
                    ),
                    HttpUrl(
                        "https://s1.ticketm.net/dam/a/c90/67a18d21-394f-4a"
                        "fe-84f9-15560d797c90_1652911_EVENT_DETAIL_PAGE_16_9.jpg"
                    ),
                ],
                sales=EventUpdateSales(
                    on_sale=True, price_max=231.38, price_min=87.63, currency="USD"
                ),
            ),
        ]
        assert get_all_events(EVENTS_SMALL) == events_list


if __name__ == "__main__":
    pytest.main()
