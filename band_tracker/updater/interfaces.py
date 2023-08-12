from typing import Protocol
from uuid import UUID

from band_tracker.db.artist_update import ArtistUpdate
from band_tracker.db.event_update import EventUpdate


class DAL(Protocol):
    async def update_artist(self, artist: ArtistUpdate) -> UUID:
        """Update an artist"""
        ...

    async def update_event(self, event: EventUpdate) -> tuple[UUID, list[UUID]]:
        """Update an event"""
        ...
