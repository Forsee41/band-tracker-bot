from typing import Any, Callable, Coroutine

import pytest
from sqlalchemy.exc import IntegrityError

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.event_update import EventUpdate
from band_tracker.db.dal import BotDAL
from band_tracker.db.dal import UpdateDAL as DAL
from band_tracker.db.models import ArtistDB


class TestAddEventDAL:
    async def test_linking_new_artists(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
    ) -> None:
        for i in ["anton", "clara", "gosha"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("fest")
        _, ids = await update_dal._add_event(update_event)
        assert len(ids) == 2

        update_event.artists += ["gosha_tm_id"]

        linked_artist_event_id = await update_dal._link_event_to_artists(
            "fest_tm_id",
            ["anton_tm_id", "clara_tm_id", "gosha_tm_id"],
        )
        new_artist = await query_artist("gosha_tm_id")
        assert new_artist
        assert linked_artist_event_id == [new_artist.event_artist[0].id]

    async def test_get_event_by_id(
        self,
        update_dal: DAL,
        bot_dal: BotDAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["gosha", "anton", "clara"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("eurovision")
        await update_dal._add_event(update_event)

        event = await update_dal._get_event_by_tm_id("eurovision_tm_id")

        assert event
        result_event = await bot_dal.get_event(event.id)
        assert result_event == event

    async def test_add_event(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("anton")
        await update_dal._add_artist(artist)

        update_event = get_event_update("concert")
        await update_dal._add_event(update_event)
        result_event = await update_dal._get_event_by_tm_id("concert_tm_id")

        assert result_event
        assert result_event.title == "concert"
        assert result_event.sales
        assert result_event.image
        assert result_event.artist_ids

    async def test_add_identical_event(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("anton")
        await update_dal._add_artist(artist)

        update_event = get_event_update("concert")

        await update_dal._add_event(update_event)
        with pytest.raises(IntegrityError):
            await update_dal._add_event(update_event)

    async def test_add_event_without_artists(
        self,
        update_dal: DAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        for i in ["gosha", "anton", "clara"]:
            artist = get_artist_update(i)
            await update_dal._add_artist(artist)

        update_event = get_event_update("eurovision")
        update_event.artists = []
        await update_dal._add_event(update_event)
        result_event = await update_dal._get_event_by_tm_id("eurovision_tm_id")
        assert result_event

    async def test_add_event_with_unknown_artists(
        self,
        update_dal: DAL,
        bot_dal: BotDAL,
        get_event_update: Callable[[str], EventUpdate],
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artists = ["gosha", "anton", "clara"]
        for i in artists:
            artist = get_artist_update(i)

            await update_dal._add_artist(artist)

        update_event = get_event_update("eurovision")
        update_event.artists += ["unknown_tm_id"]
        await update_dal._add_event(update_event)
        result_event = await update_dal._get_event_by_tm_id("eurovision_tm_id")
        assert result_event

        result_artists = await result_event.get_artists(bot_dal)
        assert [i.name for i in result_artists if i is not None] == artists


if __name__ == "__main__":
    pytest.main()
