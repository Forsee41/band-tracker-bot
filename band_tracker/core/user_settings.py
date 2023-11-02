from dataclasses import dataclass

from band_tracker.core.enums import TrackingDistance


@dataclass
class UserSettings:
    """
    A set of user-specific options.
    """

    default_tracking_distance: TrackingDistance
    autofollow: bool
    autosubscribe: bool

    @classmethod
    def default(cls: type) -> "UserSettings":
        return cls(
            default_tracking_distance=TrackingDistance.worldwide,
            autofollow=False,
            autosubscribe=False,
        )
