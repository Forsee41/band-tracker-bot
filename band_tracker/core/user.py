from dataclasses import dataclass
from datetime import datetime

from band_tracker.core.follow import Follow
from band_tracker.core.user_settings import UserSettings


@dataclass
class User:
    id: str
    name: str
    subscriptions: list[str]
    follows: list[Follow]
    join_date: datetime
    settings: UserSettings
