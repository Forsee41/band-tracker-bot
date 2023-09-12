import asyncio
import json
from typing import Callable
from unittest.mock import AsyncMock, patch

import pytest

from band_tracker.updater.errors import (
    InvalidResponseStructureError,
    InvalidTokenError,
    RateLimitViolation,
)
from band_tracker.updater.page_iterator import ApiClient, PageIterator
from band_tracker.updater.timestamp_predictor import LinearPredictor


@pytest.fixture()
def mock_response() -> Callable[[str], dict]:
    def lol(name: str = "invalid_structure_error") -> dict:
        file_path = "tests/test_data/iterator_mock"
        with open(f"{file_path}/{name}.json", "r") as f:
            response_dict = json.load(f)

        return response_dict

    return lol


@patch("band_tracker.updater.page_iterator.ApiClient.make_request")
class TestIterator:
    custom_request = ApiClient("", {})

    async def test_iteration(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_linear_predictor: Callable[[float, float], LinearPredictor],
    ) -> None:
        async def mock_make_request(page_number: int) -> dict:
            await asyncio.sleep(0.1)

            return mock_response(f"page{page_number}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = PageIterator(self.custom_request, predictor=predictor)

        data = []
        async for i in iterator:
            data.append(i)

        page_response = mock_response("page3")

        assert data[2] == page_response
        assert len(data) == 5
        assert asyncio.iscoroutinefunction(mock_make_request)

    async def test_structure_error(
        self,
        mock_get: AsyncMock,
        mock_response: Callable[[str], dict],
        get_linear_predictor: Callable[[float, float], LinearPredictor],
    ) -> None:
        async def mock_make_request(page_number: int) -> dict:
            await asyncio.sleep(0.1)

            if page_number == 3:
                """simulation of response with invalid structure on the 3. page"""

                return mock_response("invalid_structure_error")

            return mock_response(f"page{page_number}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = PageIterator(self.custom_request, predictor=predictor)

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
        async def mock_make_request(page_number: int) -> dict:
            await asyncio.sleep(0.1)

            if page_number == 1:
                """simulation of response when invalid token was given"""

                return mock_response("invalid_token")

            return mock_response(f"page{page_number}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = PageIterator(self.custom_request, predictor=predictor)

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
        async def mock_make_request(page_number: int) -> dict:
            await asyncio.sleep(0.1)

            if page_number == 4:
                """simulation of response when rate limit is exceeded"""

                return mock_response("rate_limit_error")

            return mock_response(f"page{page_number}")

        mock_get.side_effect = mock_make_request
        predictor = get_linear_predictor(-0.1, 1000)

        iterator = PageIterator(self.custom_request, predictor=predictor)

        data = []
        with pytest.raises(RateLimitViolation):
            async for i in iterator:
                data.append(i)
