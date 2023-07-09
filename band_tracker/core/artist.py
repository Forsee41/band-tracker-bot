from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from band_tracker.core.interfaces import DAL

if TYPE_CHECKING:
    from band_tracker.core.event import Event


@dataclass
class ArtistSocials:
    instagram: str | None
    youtube: str | None
    spotify: str | None


@dataclass
class Artist:
    id: UUID
    name: str
    socials: ArtistSocials
    tickets_link: str | None = None
    images: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)

    def get_events(self, dal: DAL) -> list["Event"]:
        assert dal
        raise NotImplementedError

    @property
    def upcoming_events_cnt(self) -> int:
        return len(self.event_ids)
