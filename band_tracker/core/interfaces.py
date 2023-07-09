from typing import TYPE_CHECKING, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from band_tracker.core.artist import Artist


class DAL(Protocol):
    def get_artist_by_id(self, id: UUID) -> "Artist":  # type: ignore
        """Returns an artist by id"""
