import asyncio
from typing import Callable
from unittest.mock import AsyncMock, patch

import pytest
from httpx import Request, Response

from band_tracker.db.artist_update import get_description


def get_text(name: str = "normal", out: bool = False) -> str:
    if out:
        suffix: str = "_out"
    else:
        suffix: str = "_in.html"

    file_path = "tests/test_data/description_mock"
    with open(f"{file_path}/{name}{suffix}", "r") as f:
        text = f.read()

    return text


@pytest.fixture()
def get_html() -> Callable[[str], str]:
    return get_text


@patch("httpx.AsyncClient.get")
class TestDescription:
    async def test_get_description(
        self, mock_get: AsyncMock, get_html: Callable[[str], str]
    ) -> None:
        async def mock_make_request(url="") -> Response:
            await asyncio.sleep(0.1)
            html_raw = get_html(f"{url}")
            assert html_raw

            # mocking both request and response
            request = Request(method="GET", url="")
            response = Response(200, content=html_raw, request=request)
            response_html = response.text
            assert response_html == html_raw

            return response

        url = "normal"
        desire_description = get_text(out=True)

        mock_get.side_effect = mock_make_request

        result_description = await get_description(url, {"death grips"})
        assert result_description == desire_description
