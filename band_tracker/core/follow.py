from dataclasses import dataclass

from band_tracker.core.enums import Range


@dataclass
class Follow:
    artist: str
    range_: Range
    notify: bool
