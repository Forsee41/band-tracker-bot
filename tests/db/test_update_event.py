from collections.abc import Coroutine
from datetime import datetime
from typing import Any, Callable

import pytest

from band_tracker.core.enums import EventSource
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_update import UpdateDAL as DAL
from band_tracker.db.event_update import EventUpdate
from band_tracker.db.models import ArtistDB


class TestUpdateEventDAL:
    async def test_event_update(
        self,
        update_dal: DAL,
        bot_dal: BotDAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("fest")

        new_artist = get_artist_update("gosha")
        await update_dal._add_artist(new_artist)

        await update_dal._add_event(update_event)

        update_event.artists += [
            ArtistUpdate(
                name="",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "gosha_tm_id"}
                },
                tickets_link=None,
                main_image=None,
                thumbnail_image=None,
                description=None,
            )
        ]

        update_event.sales.sale_start = datetime(8045, 4, 5)
        update_event.sales.sale_end = datetime(8045, 4, 6)

        update_event.main_image = None

        await update_dal.update_event(update_event)

        result_event = await update_dal._get_event_by_tm_id("fest_tm_id")
        assert result_event
        assert result_event.image is None
        assert result_event.title == "fest"
        assert result_event.venue_country == "USA"
        assert result_event.sales.sale_start == datetime(8045, 4, 5)
        assert result_event.artist_ids

        result_artists = await result_event.get_artists(bot_dal)
        assert len(result_artists) == 3

    async def test_add_new_event(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artists = ["gosha", "anton", "clara"]
        for i in artists:
            artist = get_artist_update(i)

            await update_dal._add_artist(artist)

        update_event = get_event_update("eurovision")
        await update_dal.update_event(update_event)

        result_event = await update_dal._get_event_by_tm_id("eurovision_tm_id")
        assert result_event

    async def test_update_to_none(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("fest")
        await update_dal._add_event(update_event)

        update_event.ticket_url = None
        update_event.main_image = None
        await update_dal.update_event(update_event)

        result_event = await update_dal._get_event_by_tm_id("fest_tm_id")
        assert result_event
        assert result_event.ticket_url is None
        assert result_event.image is None

    async def test_linking_new_artists(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
    ) -> None:
        for i in ["anton", "clara"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("fest")
        await update_dal._add_event(update_event)

        update_event.artists += [
            ArtistUpdate(
                name="",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "gosha_tm_id"}
                },
                tickets_link=None,
                main_image=None,
                thumbnail_image=None,
                description=None,
            )
        ]

        linked_artist_event_id = await update_dal._link_event_to_artists(
            "fest_tm_id",
            ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
        )
        new_artist = await query_artist("gosha_tm_id")
        assert new_artist is None
        assert len(linked_artist_event_id) == 0

        new_artist2 = get_artist_update("gosha")
        await update_dal._add_artist(new_artist2)

        _, ids = await update_dal.update_event(update_event)

        new_artist = await query_artist("gosha_tm_id")
        assert new_artist
        assert set(ids) == {new_artist.event_artist[0].id}

        linked_artist = await update_dal._link_event_to_artists(
            "fest_tm_id",
            ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
        )
        assert linked_artist == []

    async def test_add_artists_from_updated_event(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
    ) -> None:
        update_event = get_event_update("fest")
        await update_dal._add_event(update_event)

        initArtist = await update_dal.get_artist_by_tm_id("anton_tm_id")
        assert initArtist

        update_event.artists += [
            ArtistUpdate(
                name="",
                source_specific_data={
                    EventSource.ticketmaster_api: {"id": "gosha_tm_id"}
                },
                tickets_link=None,
                main_image=None,
                thumbnail_image=None,
                description=None,
            )
        ]
        await update_dal.update_event(update_event)
        newArtist = await update_dal.get_artist_by_tm_id("gosha_tm_id")
        assert newArtist


if __name__ == "__main__":
    pytest.main()
