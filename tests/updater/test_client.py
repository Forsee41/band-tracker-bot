from datetime import datetime

import pytest

from band_tracker.core.enums import EventSource
from band_tracker.db.artist_update import ArtistUpdate, ArtistUpdateSocials
from band_tracker.db.event_update import EventUpdate, EventUpdateSales
from band_tracker.updater.deserializator import (
    get_all_artists,
    get_all_events,
    get_artist,
    get_event,
)
from tests.test_data.client_mock.temp_const import (
    ARTISTS,
    ARTISTS_SMALL,
    EVENTS,
    EVENTS_SMALL,
)


class TestClient:
    @pytest.mark.parametrize(
        "raw_artist, expected_artist",
        [
            (
                ARTISTS.get("_embedded").get("attractions")[0],
                ArtistUpdate(
                    name="The Orb",
                    socials=ArtistUpdateSocials(
                        spotify="https://open.spotify.com/artist"
                        "/5HAtRoEPUvGSA7ziTGB1cF?autoplay=true",
                        instagram="http://www.instagram.com/theorblive",
                        youtube="https://www.youtube.com"
                        "/channel/UCpoyFBLTLfbT2Z1D1AnlvLg",
                        wiki="https://en.wikipedia.org/wiki/The_Orb",
                    ),
                    aliases=[],
                    tickets_link="https://www.ticketmaster.com"
                    "/the-orb-tickets/artist/806748",
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171RCf"}
                    },
                    genres=["Rock", "Pop"],
                    main_image="https://s1.ticketm.net/dam/a/5a1/"
                    "d9a78cdb-a7ce-4e40-861d-4ad1c6b355a1_"
                    "264701_RETINA_PORTRAIT_3_2.jpg",
                    thumbnail_image="https://s1.ticketm.net/dam/"
                    "a/5a1/d9a78cdb-a7ce-4e40-861d-4ad1c"
                    "6b355a1_264701_RECOMENDATION_16_9.jpg",
                    description=None,
                ),
            ),
            (
                ARTISTS.get("_embedded").get("attractions")[1],
                ArtistUpdate(
                    name="Jeff Tain Watts",
                    tickets_link="https://www.ticketmaster.com/"
                    "jeff-tain-watts-tickets/artist/844673",
                    socials=ArtistUpdateSocials(
                        **{
                            "spotify": None,
                            "youtube": None,
                            "instagram": None,
                            "wiki": None,
                        }
                    ),
                    source_specific_data={
                        EventSource.ticketmaster_api: {"id": "K8vZ9171OI0"}
                    },
                    aliases=[],
                    genres=["Jazz", "Jazz"],
                    main_image="https://s1.ticketm.net/dam/c/bea/"
                    "03d47f66-d37b-4aca-aa17-0135be64dbea_1"
                    "05801_RETINA_PORTRAIT_3_2.jpg",
                    thumbnail_image="https://s1.ticketm.net/dam/"
                    "c/bea/03d47f66-d37b-4aca-"
                    "aa17-0135be64dbea_105801_RECOMENDATIO"
                    "N_16_9.jpg",
                    description=None,
                ),
            ),
        ],
    )
    def test_get_artist(self, raw_artist: dict, expected_artist: ArtistUpdate) -> None:
        assert get_artist(raw_artist) == expected_artist

    def test_get_event(self) -> None:
        raw_event = EVENTS.get("_embedded").get("events")[0]
        event = EventUpdate(
            title="Shania Twain: Queen Of Me Tour",
            date=datetime(2023, 7, 15),
            venue="Ruoff Music Center",
            ticket_url="https://concerts.livenation.com/shania-twain-queen-of-me-tour-"
            "noblesville-indiana-07-15-2023/event/05005D55DD6D454E",
            source_specific_data={
                EventSource.ticketmaster_api: {"id": "vvG1fZ949qhf4C"}
            },
            venue_city="Noblesville",
            venue_country="United States Of America",
            artists=["K8vZ91719n0", "K8vZ917_bOf"],
            main_image="https://s1.ticketm.net/dam/a/1d1/47cc9b10-4904-"
            "4dec-b1d6-539e44a521d1_1825531_RETINA_PORTRAIT_3_2.jpg",
            thumbnail_image="https://s1.ticketm.net/dam/a/1d1/47cc9b10-"
            "4904-4dec-b1d6-539e44a521d1_1825531_RECOMEND"
            "ATION_16_9.jpg",
            sales=EventUpdateSales(
                sale_start=datetime(2022, 11, 4),
                sale_end=datetime(2023, 7, 16),
                price_max=249.95,
                price_min=39.95,
                currency="USD",
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
                    wiki=None,
                ),
                aliases=[],
                tickets_link="https://www.ticketmaster.com/solina"
                "-celloensemble-tickets/artist/2772347",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "K8vZ917_Fi7"}
                },
                genres=["Classical", "Classical/Vocal"],
                main_image="https://s1.ticketm.net/dam/c/518/83a05c63-479c-"
                "4f7e-a7aa-1932aab77518_105461_RETINA_PORTRAIT_3_2.jpg",
                thumbnail_image="https://s1.ticketm.net/dam/c/518/83a05c63-479c-4f7e"
                "-a7aa-1932aab77518_105461_RECOMENDATION_16_9.jpg",
                description=None,
            ),
            ArtistUpdate(
                name="Maze featuring Frankie Beverly",
                socials=ArtistUpdateSocials(
                    spotify=None,
                    instagram=None,
                    youtube=None,
                    wiki=None,
                ),
                aliases=["frankie beverly and maze", "maze frankie beverly"],
                tickets_link="https://www.ticketmaster.com/maze-f"
                "eaturing-frankie-beverly-tickets/artist/735607",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "K8vZ9171Idf"}
                },
                genres=["R&B", "Soul"],
                main_image="https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-b884-"
                "4406b8ab64cd_1600911_RETINA_PORTRAIT_3_2.jpg",
                thumbnail_image="https://s1.ticketm.net/dam/a/4cd/f4b129cc-7197-4ff0-b"
                "884-4406b8ab64cd_1600911_RECOMENDATION_16_9.jpg",
                description=None,
            ),
        ]
        assert get_all_artists(ARTISTS_SMALL) == artists_list

    def test_get_all_events(self) -> None:
        events_list = [
            EventUpdate(
                title="Shania Twain: Queen Of Me Tour",
                date=datetime(2023, 7, 15),
                venue="Ruoff Music Center",
                ticket_url="https://concerts.livenation."
                "com/shania-twain-queen-of-me-tour-"
                "noblesville-indiana-07-15-2023/event/05005D55DD6D454E",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "vvG1fZ949qhf4C"}
                },
                venue_city="Noblesville",
                venue_country="United States Of America",
                artists=["K8vZ91719n0", "K8vZ917_bOf"],
                main_image="https://s1.ticketm.net/dam/a/1d1/47cc9b10-"
                "4904-4dec-b1d6-539e44a521d1_1825531_RETINA_PORTRAIT_3_2.jpg",
                thumbnail_image="https://s1.ticketm.net/dam/a/1d1/47cc9b10-49"
                "04-4dec-b1d6-539e44a521d1_1825531_R"
                "ECOMENDATION_16_9.jpg",
                sales=EventUpdateSales(
                    sale_start=datetime(2022, 11, 4),
                    sale_end=datetime(2023, 7, 16),
                    price_max=249.95,
                    price_min=39.95,
                    currency="USD",
                ),
            ),
            EventUpdate(
                title="Imagine Dragons",
                date=datetime(2023, 7, 8),
                venue="American Family Insurance Amphitheater - Summerfest Grounds",
                ticket_url="https://www.ticketmaster.com/imagine-dragon"
                "s-milwaukee-wisconsin-07-08-20"
                "23/event/07005D689BED1C00",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "vvG1jZ9pxhDoYZ"}
                },
                venue_city="Milwaukee",
                venue_country="United States Of America",
                artists=["K8vZ917GSz7"],
                main_image="https://s1.ticketm.net/dam/a/c90/67a18d21-394f"
                "-4afe-84f9-15560d797c90_1652911_RETINA_PORTRAIT_3_2.jpg",
                thumbnail_image="https://s1.ticketm.net/dam/a/c90/67a18"
                "d21-394f-4afe-84f9-15560d797c90_16529"
                "11_RECOMENDATION_16_9.jpg",
                sales=EventUpdateSales(
                    sale_start=datetime(2022, 11, 18),
                    sale_end=datetime(2023, 7, 9),
                    price_max=231.38,
                    price_min=87.63,
                    currency="USD",
                ),
            ),
        ]
        assert get_all_events(EVENTS_SMALL) == events_list


if __name__ == "__main__":
    pytest.main()
