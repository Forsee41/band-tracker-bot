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
