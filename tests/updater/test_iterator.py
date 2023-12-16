import asyncio
import json
from datetime import datetime, timedelta
from typing import Callable
from unittest.mock import AsyncMock, patch

import pytest

from band_tracker.updater.api_client import ApiClientEvents
from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitViolation,
)
from band_tracker.updater.page_iterator import EventIterator
from band_tracker.updater.timestamp_predictor import LinearPredictor, TimestampPredictor


@pytest.fixture()
def mock_response() -> Callable[[str], dict]:
    def lol(name: str = "invalid_structure_error") -> dict:
        file_path = "tests/test_data/iterator_mock"
        with open(f"{file_path}/{name}.json", "r") as f:
            response_dict = json.load(f)

        return response_dict

    return lol


@patch("band_tracker.updater.api_client.ApiClientEvents.make_request")
class TestIterator:
    custom_request = ApiClientEvents("", {}, [])

    async def test_chunk_progression(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_timestamp_predictor: Callable[[timedelta], TimestampPredictor],
    ) -> None:
        async def mock_make_request(
            start_date: datetime,
            end_date: datetime,
            page_number: int = 0,
            country_code: str = "",
        ) -> dict:
            await asyncio.sleep(0.1)
            return mock_response(f"page{page_number + 1}")

        mock_get.side_effect = mock_make_request

        predictor = get_timestamp_predictor(timedelta(days=365))
        iterator = EventIterator(self.custom_request, predictor=predictor)
        initial_max_date = iterator.max_end_time

        async for i in iterator:
            pass

        chunks = iterator.chunks

        assert len(chunks) == 2
        assert iterator.all_chunks_done() is True
        assert iterator.max_end_time > initial_max_date

    @pytest.mark.slow
    async def test_process_large_chunk(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_timestamp_predictor: Callable[[timedelta], TimestampPredictor],
    ) -> None:
        async def mock_make_request(
            start_date: datetime,
            end_date: datetime,
            page_number: int = 0,
            country_code: str = "",
        ) -> dict:
            await asyncio.sleep(0.1)

            if country_code == "US" or country_code == "BR" or country_code == "":
                return mock_response("large_page")
            else:
                return mock_response("processed_page")

        mock_get.side_effect = mock_make_request

        predictor = get_timestamp_predictor(timedelta(days=0))
        iterator = EventIterator(self.custom_request, predictor=predictor)
        iterator.max_end_time += timedelta(days=731)

        async for i in iterator:
            pass

        assert len(iterator.chunks) == 2

    async def test_structure_error(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_linear_predictor: Callable[[float, float], LinearPredictor],
    ) -> None:
        async def mock_make_request(
            start_date: datetime,
            end_date: datetime,
            page_number: int = 0,
            country_code: str = "",
        ) -> dict:
            await asyncio.sleep(0.1)
            if page_number == 3:
                """simulation of response when invalid structure was given"""

                return mock_response("invalid_structure_error")

            return mock_response(f"page{page_number + 1}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = EventIterator(self.custom_request, predictor=predictor)

        data = []
        with pytest.raises(InvalidResponseStructureError):
            async for i in iterator:
                data.append(i)

    async def test_token_error(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_linear_predictor: Callable[[float, float], LinearPredictor],
    ) -> None:
        async def mock_make_request(
            start_date: datetime,
            end_date: datetime,
            page_number: int = 0,
            country_code: str = "",
        ) -> dict:
            await asyncio.sleep(0.1)

            if page_number == 3:
                """simulation of response when invalid token was given"""

                return mock_response("invalid_token")

            return mock_response(f"page{page_number + 1}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = EventIterator(self.custom_request, predictor=predictor)

        data = []
        with pytest.raises(InvalidTokenError):
            async for i in iterator:
                data.append(i)

    async def test_rate_limit_error(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_linear_predictor: Callable[[float, float], LinearPredictor],
    ) -> None:
        async def mock_make_request(
            start_date: datetime,
            end_date: datetime,
            page_number: int = 0,
            country_code: str = "",
        ) -> dict:
            await asyncio.sleep(0.1)

            if page_number == 3:
                """simulation of response when rate limit is exceeded"""

                return mock_response("rate_limit_error")

            return mock_response(f"page{page_number + 1}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = EventIterator(self.custom_request, predictor=predictor)

        data = []
        with pytest.raises(RateLimitViolation):
            async for i in iterator:
                data.append(i)
