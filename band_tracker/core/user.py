from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from band_tracker.core.follow import Follow
from band_tracker.core.user_settings import UserSettings


@dataclass
class User:
    id: UUID
    tg_id: int
    name: str
    follows: dict[UUID, Follow]
    join_date: datetime
    settings: UserSettings


@dataclass
class RawUser:
    tg_id: int
    name: str
    follows: dict[UUID, Follow]
    join_date: datetime
    settings: UserSettings
