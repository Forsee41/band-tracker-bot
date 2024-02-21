import logging
import re
from typing import Any, TypeAlias
from urllib.parse import urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, StrictStr, field_validator

from band_tracker.core.enums import EventSource

SourceSpecificArtistData: TypeAlias = dict[EventSource, dict[str, Any]]

log = logging.getLogger(__name__)


async def get_description(url: str, key_words: set[str]) -> str | None:
    # to skip httpx redirection
    parsed_url = urlparse(url)
    if parsed_url.scheme == "http":
        url = urlunparse(("https",) + parsed_url[1:])

    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(5):
            try:
                response = await client.get(url)
                response.raise_for_status()

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                content_div = soup.find("div", {"id": "mw-content-text"})
                if not content_div:
                    log.error("Could not find content div")
                    return None

                content_text = content_div.find(
                    "div", {"class": "mw-parser-output"}  # type: ignore
                )

                if not content_text or isinstance(content_text, int):
                    log.error("Could not find the right div class")
                    return None

                find_params = {"class_": False, "id": False}
                first_paragraph = content_text.find("p", **find_params)

                log.debug(first_paragraph)
                if not first_paragraph or isinstance(first_paragraph, int):
                    return None

                flatten_text = re.sub(r"\([^)]*\)", "", first_paragraph.get_text())
                text_without_references = re.sub(r"\[\d+\]", "", flatten_text).strip()

                # excluding potentially irrelevant content to avoid data noise
                if any(
                    key_word in text_without_references.lower()
                    for key_word in key_words
                ):
                    return text_without_references
                else:
                    log.warning(
                        "description text does not contain any artist reference"
                    )
                    return None
            except httpx.TimeoutException as e:
                log.warning(e)
                continue
            except Exception as e:
                log.error(e)
                return None
        else:
            log.error("TIMEOUT")
            raise httpx.TimeoutException("Wiki Timeout")


class ArtistUpdateSocials(BaseModel):
    instagram: str | None
    youtube: str | None
    spotify: str | None
    wiki: str | None


class ArtistUpdate(BaseModel):
    name: StrictStr
    socials: ArtistUpdateSocials = ArtistUpdateSocials(
        instagram=None, youtube=None, spotify=None, wiki=None
    )
    tickets_link: str | None = Field(None)
    source_specific_data: SourceSpecificArtistData = Field(
        {EventSource.ticketmaster_api: {}}
    )
    main_image: str | None = Field(None)
    thumbnail_image: str | None = Field(None)
    genres: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    description: str | None = Field(None)

    @field_validator("source_specific_data")
    def id_presence(
        cls,
        _source_specific_data_value: SourceSpecificArtistData,
    ) -> dict[EventSource, dict]:
        ticketmaster_data = _source_specific_data_value.get(
            EventSource.ticketmaster_api
        )
        ticketmaster_id = ticketmaster_data["id"] if ticketmaster_data else None
        if not ticketmaster_id:
            raise ValueError("Update should have source-specific id")
        return _source_specific_data_value

    @field_validator("genres")
    def unique_genres(cls, value: list[str]) -> list[str]:
        return list(set(value))

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Artist (like specific id, slug, etc.),
        or an empty dict if one is not present
        """
        if source in self.source_specific_data:
            return self.source_specific_data[source]
        else:
            return {}

    async def set_description(self) -> None:
        wiki = self.socials.wiki
        if wiki:
            key_words = set([self.name] + self.aliases)
            self.description = await get_description(
                wiki, {i.lower() for i in key_words}
            )
        else:
            self.description = None
