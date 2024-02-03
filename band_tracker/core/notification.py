from dataclasses import dataclass

from band_tracker.core.artist import Artist
from band_tracker.core.event import Event
from band_tracker.core.user import User


@dataclass
class Notification:
    event: Event
    user: User
    target_artists: list[Artist]
    other_artists: list[Artist]
    is_first: bool
