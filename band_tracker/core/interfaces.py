from typing import TYPE_CHECKING, Optional, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from band_tracker.core.artist import Artist


class DAL(Protocol):
    async def get_artist(self, id: UUID) -> Optional["Artist"]:
        """Returns an artist by id"""
