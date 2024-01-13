from typing import Any, Callable, Coroutine

import pytest
from sqlalchemy.exc import IntegrityError

from band_tracker.core.enums import EventSource
from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.dal_update import UpdateDAL as DAL
from band_tracker.db.models import ArtistDB, GenreDB


class TestAddArtistDAL:
    async def test_add_artist(
        self, update_dal: DAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist = get_artist_update("gosha")
        await update_dal._add_artist(artist)
        result_artist = await update_dal.get_artist_by_tm_id("gosha_tm_id")

        assert result_artist
        assert result_artist.name == "gosha"
        assert result_artist.tickets_link == "https://gosha_tickets.com"

    async def test_same_tm_id_fails(
        self, update_dal: DAL, get_artist_update: Callable[[str], ArtistUpdate]
    ) -> None:
        artist_1 = get_artist_update("gosha")
        artist_2 = get_artist_update("clara")
        artist_2.source_specific_data[EventSource.ticketmaster_api][
            "id"
        ] = "gosha_tm_id"
        await update_dal._add_artist(artist_1)
        with pytest.raises(IntegrityError):
            await update_dal._add_artist(artist_2)

    async def test_aliases_added(
        self,
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await update_dal._add_artist(artist)
        result_db_artist = await query_artist(artist_tm_id)
        assert result_db_artist
        result_aliases = [alias.alias for alias in result_db_artist.aliases]
        assert set(result_aliases) == set(artist.aliases)

    async def test_description_added(
        self,
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
    ) -> None:
        artist = get_artist_update("gosha")
        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        await artist.set_description()
        await update_dal._add_artist(artist)
        result_db_artist = await query_artist(artist_tm_id)

        assert result_db_artist
        assert result_db_artist.description

    async def test_genres_added(
        self,
        update_dal: DAL,
        get_artist_update: Callable[[str], ArtistUpdate],
        query_artist: Callable[[str], Coroutine[Any, Any, ArtistDB | None]],
        query_genre: Callable[[str], Coroutine[Any, Any, GenreDB | None]],
    ) -> None:
        artist = get_artist_update("gosha")
        await update_dal._add_artist(artist)

        result_artist = await update_dal.get_artist_by_tm_id("gosha_tm_id")

        artist_tm_id = artist.source_specific_data[EventSource.ticketmaster_api]["id"]
        result_db_artist = await query_artist(artist_tm_id)

        assert result_artist
        assert result_db_artist
        for genre in result_db_artist.genres:
            db_genre = await query_genre(str(genre.id))
            assert db_genre
            assert db_genre.name in set(result_artist.genres)

        assert set(result_artist.genres) == {"rock", "heavy-metal"}


if __name__ == "__main__":
    pytest.main()
