from dataclasses import dataclass

from band_tracker.core.enums import EventSource, Genre


@dataclass
class Artist:
    id: str
    name: str
    shortname: str | None
    spotify_link: str | None
    link: str | None
    upcoming_events_amount: int
    score: float
    genres: list[Genre]
    _source_specific_data: dict[EventSource, dict]

    def get_source_specific_data(self, source: EventSource) -> dict:
        """
        Returns a source-specific data of an Artist (like specific id, slug, etc.),
        or an empty dict if one is not present
        """
        if source in self._source_specific_data:
            return self._source_specific_data[source]
        else:
            return {}

    @property
    def has_upcoming_events(self) -> bool:
        return self.upcoming_events_amount > 0
