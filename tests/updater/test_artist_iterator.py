import asyncio
from typing import Callable
from unittest.mock import AsyncMock, patch

import pytest

from band_tracker.updater.api_client import ApiClientArtists
from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitViolation,
    UnexpectedFaultResponseError,
)
from band_tracker.updater.page_iterator import ArtistIterator, ArtistProgression


@patch("band_tracker.updater.api_client.ApiClientArtists.make_request")
class TestArtistIterator:
    custom_request = ApiClientArtists("", {}, [])

    @pytest.mark.slow
    async def test_keyword_search_progression(
        self,
        mock_request: AsyncMock,
        mock_response: Callable[[str], dict],
    ) -> None:
        async def mock_make_request(keyword: str = "", tm_id: str = "") -> dict:
            await asyncio.sleep(0.1)
            return mock_response(f"page{keyword}")

        mock_request.side_effect = mock_make_request

        keywords = ["1", "2", "3"]
        iterator = ArtistIterator(self.custom_request, keywords)

        async for i in iterator:
            pass

        artist_progression = [
            True
            for artist in iterator.artists
            if artist.progression is ArtistProgression.done
        ]
        assert all(artist_progression)

    @pytest.mark.slow
    async def test_structure_error(
        self,
        mock_request: AsyncMock,
        mock_response: Callable[[str], dict],
    ) -> None:
        async def mock_make_request(keyword: str = "", tm_id: str = "") -> dict:
            await asyncio.sleep(0.1)
            if keyword == "2":
                """simulation of response when invalid structure was given"""
                return mock_response("invalid_structure_error")

            return mock_response(f"page{keyword}")

        mock_request.side_effect = mock_make_request
        keywords = ["1", "2", "3"]
        iterator = ArtistIterator(self.custom_request, keywords)

        with pytest.raises(InvalidResponseStructureError):
            async for i in iterator:
                pass

    @pytest.mark.slow
    async def test_rate_limit_error(
        self,
        mock_request: AsyncMock,
        mock_response: Callable[[str], dict],
    ) -> None:
        async def mock_make_request(keyword: str = "", tm_id: str = "") -> dict:
            await asyncio.sleep(0.1)
            if keyword == "1":
                """simulation of response when rate limit is exceeded"""

                return mock_response("rate_limit_error")

            return mock_response(f"page{keyword}")

        mock_request.side_effect = mock_make_request
        keywords = ["1", "2", "3"]
        iterator = ArtistIterator(self.custom_request, keywords)

        with pytest.raises(RateLimitViolation):
            async for i in iterator:
                pass

    @pytest.mark.slow
    async def test_token_error(
        self,
        mock_request: AsyncMock,
        mock_response: Callable[[str], dict],
    ) -> None:
        async def mock_make_request(keyword: str = "", tm_id: str = "") -> dict:
            await asyncio.sleep(0.1)
            if keyword == "3":
                """simulation of response when invalid token was given"""

                return mock_response("invalid_token")

            return mock_response(f"page{keyword}")

        mock_request.side_effect = mock_make_request
        keywords = ["1", "2", "3"]
        iterator = ArtistIterator(self.custom_request, keywords)

        with pytest.raises(InvalidTokenError):
            async for i in iterator:
                pass

    @pytest.mark.slow
    async def test_unexpected_error(
        self,
        mock_request: AsyncMock,
        mock_response: Callable[[str], dict],
    ) -> None:
        async def mock_make_request(keyword: str = "", tm_id: str = "") -> dict:
            await asyncio.sleep(0.1)
            if keyword == "3":
                """simulation of unexpected error"""

                return mock_response("unexpected_error")

            return mock_response(f"page{keyword}")

        mock_request.side_effect = mock_make_request
        keywords = ["1", "2", "3"]
        iterator = ArtistIterator(self.custom_request, keywords)

        with pytest.raises(UnexpectedFaultResponseError):
            async for i in iterator:
                pass
