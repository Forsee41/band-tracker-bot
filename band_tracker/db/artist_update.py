import logging
import re
from typing import Any, TypeAlias

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag
from pydantic import BaseModel, Field, StrictStr, field_validator

from band_tracker.core.enums import EventSource
from band_tracker.updater.errors import DescriptionFetchError

SourceSpecificArtistData: TypeAlias = dict[EventSource, dict[str, Any]]

log = logging.getLogger(__name__)


async def get_description(url: str) -> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        if response.status_code != 200:
            raise DescriptionFetchError(
                f"Failed to fetch the page. Status code: {response.status_code}"
            )

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        content_div: Tag | None | NavigableString = soup.find(
            "div", {"id": "mw-content-text"}
        )
        if not content_div:
            raise DescriptionFetchError("Could not find content div")

        content_text: Tag | None = content_div.find(
            "div", {"class": "mw-parser-output"}
        )

        if not content_text or isinstance(content_text, int):
            raise DescriptionFetchError("Could not find right div class")

        first_paragraph: Tag | None = content_text.find(
            "p", class_=False, id=False  # type: ignore
        )  # type: ignore

        log.debug(first_paragraph)
        if not first_paragraph:
            return None

        text = re.sub(r"\[\d+\]", "", first_paragraph.get_text())
        return text.strip()


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
            self.description = await get_description(wiki)
        else:
            self.description = None
