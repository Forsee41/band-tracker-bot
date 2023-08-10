from copy import copy
from typing import Any, Callable, Coroutine

import pytest
from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from band_tracker.core.artist_update import ArtistUpdate
from band_tracker.core.enums import EventSource
from band_tracker.db.dal import DAL
from band_tracker.db.models import ArtistDB, ArtistTMDataDB


class TestUpdateArtistDAL:
    async def test_artist_not_added_if_exists(
        self,
        dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist2 = get_artist_update("anton")
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        artist2.source_specific_data[EventSource.ticketmaster_api]["id"] = artist_tm_id
        await dal.update_artist(artist)
        await dal.update_artist(artist2)
        stmt = (
            select(ArtistDB)
            .join(ArtistTMDataDB)
            .where(ArtistTMDataDB.id == artist_tm_id)
        )
        async with dal.sessionmaker.session() as session:
            session: AsyncSession
            result = await session.scalars(stmt)
            assert len(result.all()) == 1

    async def test_artist_added_if_new(
        self,
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        result_query = await query_artist(artist_tm_id)
        assert result_query is None
        await dal.update_artist(artist)
        result_db_artist = await query_artist(artist_tm_id)
        assert result_db_artist
        assert result_db_artist.name == "gosha"

    async def test_artist_fields_updated(
        self, dal: DAL, get_artist_update: Callable[[], ArtistUpdate]
    ) -> None:
        artist = get_artist_update()
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal._add_artist(artist)
        artist.name = "new_artist_name"
        await dal.update_artist(artist)
        queried_artist = await dal.get_artist(tm_id)
        assert queried_artist
        assert queried_artist.name == "new_artist_name"

    async def test_socials_updated(
        self, dal: DAL, get_artist_update: Callable[[], ArtistUpdate]
    ) -> None:
        artist = get_artist_update()
        tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal._add_artist(artist)
        artist.socials.instagram = HttpUrl("https://new_artist_instagram.com/")
        artist.socials.spotify = HttpUrl("https://new_artist_spotify.com/")
        artist.socials.youtube = HttpUrl("https://new_artist_youtube.com/")
        await dal.update_artist(artist)
        queried_artist = await dal.get_artist(tm_id)
        assert queried_artist
        assert queried_artist.socials.instagram == "https://new_artist_instagram.com/"
        assert queried_artist.socials.spotify == "https://new_artist_spotify.com/"
        assert queried_artist.socials.youtube == "https://new_artist_youtube.com/"

    async def test_aliases_updated(
        self,
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal._add_artist(artist)
        artist.aliases.append("new_alias")
        await dal.update_artist(artist)
        result_db_artist = await query_artist(artist_tm_id)
        assert result_db_artist
        result_aliases = [alias.alias for alias in result_db_artist.aliases]
        assert set(result_aliases) == set(artist.aliases)

    async def test_aliases_not_removed(
        self,
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist_old_aliases = copy(artist.aliases)
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await dal._add_artist(artist)
        artist.aliases.pop()
        await dal.update_artist(artist)
        result_db_artist = await query_artist(artist_tm_id)
        assert result_db_artist
        result_aliases = [alias.alias for alias in result_db_artist.aliases]
        assert set(result_aliases) == set(artist_old_aliases)


if __name__ == "__main__":
    pytest.main()
