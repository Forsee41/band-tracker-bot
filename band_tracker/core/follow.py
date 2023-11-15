from dataclasses import dataclass
from uuid import UUID

from band_tracker.core.enums import Range


@dataclass
class Follow:
    artist: UUID
    range_: Range
    notify: bool
