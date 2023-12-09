import logging
from abc import ABC, abstractmethod
from datetime import datetime

import httpx

from band_tracker.updater.errors import (
    AllTokensViolation,
    InvalidResponseStructureError,
    InvalidTokenError,
    QuotaViolation,
    RateLimitViolation,
    UnexpectedFaultResponseError,
)

log = logging.getLogger(__name__)


def exception_helper(data: dict[str, dict]) -> dict[str, int]:
    try:
        page_info = data.get("page")
        pages_number = page_info.get("totalPages")  # type: ignore
        elements_number = page_info.get("totalElements")  # type: ignore

        log.debug(str(pages_number) + " " + str(elements_number))
        if pages_number is None:
            raise InvalidResponseStructureError(
                f"Pages information not found in response: {page_info}"
            )

        if elements_number is None:
            raise InvalidResponseStructureError(
                f"Total elements information not found in response: {page_info}"
            )

        return {"pages_number": pages_number, "elements_number": elements_number}

    except AttributeError:
        try:
            error_response = data.get("fault", {})
            detail = error_response.get("detail", {})
            error_message = detail.get("errorcode")
            match error_message:
                case None:
                    raise InvalidResponseStructureError(
                        f"Unexpected Error, "
                        f"fault string not found in response: {error_response}"
                    )
                case "oauth.v2.InvalidApiKey":
                    raise InvalidTokenError()
                case "policies.ratelimit.SpikeArrestViolation":
                    raise RateLimitViolation()
                case "policies.ratelimit.QuotaViolation":
                    raise QuotaViolation()
                case _:
                    log.debug("edge case catch")
                    raise UnexpectedFaultResponseError(
                        f"Unexpected response fault message: {error_message}"
                    )
        except AttributeError:
            raise InvalidResponseStructureError(f"Invalid JSON structure: {data}")


class ApiClient(ABC):
    def __init__(
        self, url: str, query_params: dict[str, str], tokens: list[str]
    ) -> None:
        self.url = url
        self.query_params = query_params
        self.tokens = tokens
        self.retries = 5
        self.timeout = httpx.Timeout(5.0, pool=5)
        self.change_token_flag = False

    @abstractmethod
    async def make_request(self, **kwargs) -> None:
        if self.change_token_flag:
            await self._change_token()
            self.change_token_flag = True

    async def _change_token(self) -> None:
        for token in self.tokens:
            try:
                self.query_params.update({"apikey": token})
                response = httpx.get(self.url, params=self.query_params).json()
                exception_helper(response)
                log.debug(
                    "+++++++++++++++++++++++++++  TOKEN SWAP  +++++++++++++++++++++++++++"
                )
                return
            except QuotaViolation:
                continue
        raise AllTokensViolation


class ApiClientEvents(ApiClient):
    async def make_request(
        self,
        start_date: datetime,
        end_date: datetime,
        page_number: int = 0,
        country_code: str = "",
    ) -> dict[str, dict]:
        log.debug(
            "+++++++++++++++++++++++++++  SEND REQUEST  +++++++++++++++++++++++++++"
        )

        reformatted_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        reformatted_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        startEndDateTime = f"{reformatted_start_date},{reformatted_end_date}"
        log.debug(startEndDateTime)

        for _ in range(self.retries):
            try:
                response = httpx.get(
                    self.url,
                    params={
                        **self.query_params,
                        "startEndDateTime": startEndDateTime,
                        "page": page_number,
                        "countryCode": country_code,
                    },
                )
                return response.json()
            except httpx.TimeoutException:
                log.warning("TIMEOUT CATCH")
                continue
        else:
            log.error("TIMEOUT")
            raise httpx.TimeoutException


class ApiClientArtists(ApiClient):
    async def make_request(self, keyword: str) -> dict[str, dict]:
        log.debug(
            "+++++++++++++++++++++++++++  SEND REQUEST  +++++++++++++++++++++++++++"
        )
        for _ in range(self.retries):
            try:
                response = httpx.get(
                    self.url,
                    params={
                        **self.query_params,
                        "keyword": keyword,
                    },
                    timeout=self.timeout,
                )
                return response.json()
            except httpx.TimeoutException:
                log.warning("TIMEOUT CATCH")
                continue
        else:
            log.error("TIMEOUT")
            raise httpx.TimeoutException
