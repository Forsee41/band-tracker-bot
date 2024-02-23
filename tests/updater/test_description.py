import asyncio
from typing import Callable
from unittest.mock import AsyncMock, patch

import pytest
from httpx import Request, Response

from band_tracker.db.artist_update import get_description


def get_text(name: str = "normal", out: bool = False) -> str:
    suffix: str = ".html"
    if out:
        suffix = "_out"

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
        async def mock_make_request(url: str = "") -> Response:
            await asyncio.sleep(0.1)
            html_raw = get_html(f"{url}")
            assert html_raw

            # mocking both request and response
            request = Request(method="GET", url="")
            response = Response(200, content=html_raw, request=request)
            response_html = response.text
            assert response_html == html_raw

            return response

        desire_description = get_text(out=True)

        mock_get.side_effect = mock_make_request

        result_description = await get_description("normal", {"death grips"})
        assert result_description == desire_description

    async def test_references_missing(
        self, mock_get: AsyncMock, get_html: Callable[[str], str]
    ) -> None:
        async def mock_make_request(url: str = "") -> Response:
            await asyncio.sleep(0.1)
            html_raw = get_html(f"{url}")
            assert html_raw

            # mocking both request and response
            request = Request(method="GET", url="")
            response = Response(200, content=html_raw, request=request)
            response_html = response.text
            assert response_html == html_raw

            return response

        mock_get.side_effect = mock_make_request

        result_description = await get_description("normal", {"missing_references"})
        assert result_description is None

    async def test_wrong_html_structure(
        self, mock_get: AsyncMock, get_html: Callable[[str], str]
    ) -> None:
        async def mock_make_request(url: str = "") -> Response:
            await asyncio.sleep(0.1)
            html_raw = get_html(f"{url}")
            assert html_raw

            # mocking both request and response; 504 Gateway Timeout
            request = Request(method="GET", url="")
            response = Response(200, content=html_raw, request=request)
            response_html = response.text
            assert response_html == html_raw

            return response

        mock_get.side_effect = mock_make_request

        wrong_structure = await get_description("wrong_structure", {"death grips"})
        assert wrong_structure is None

        id_missing = await get_description(
            "mw-content-text_id_missing", {"death grips"}
        )
        assert id_missing is None

        class_missing = await get_description(
            "mw-parser-output_class_missing", {"death grips"}
        )
        assert class_missing is None

    async def test_response_error(
        self, mock_get: AsyncMock, get_html: Callable[[str], str]
    ) -> None:
        async def mock_bad_response(url: str = "") -> Response:
            await asyncio.sleep(0.1)

            # mocking both request and response; imitating 500 Internal Server Error
            request = Request(method="GET", url="")
            response = Response(500, request=request)

            return response

        mock_get.side_effect = mock_bad_response

        result_description = await get_description("", {"death grips"})
        assert result_description is None
