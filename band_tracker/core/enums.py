from enum import Enum, auto


class Range(Enum):
    CITY = "CITY"
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    WORLDWIDE = "WORLDWIDE"


class EventSource(Enum):
    ticketmaster_api = "ticketmaster_api"


class TrackingDistance(Enum):
    city = "city"
    country = "country"
    region = "region"
    worldwide = "worldwide"


class AdminNotificationLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MessageType(Enum):
    TEST = auto()
    NOTIFICATION = auto()
    HELP = auto()
    START = auto()
    MENU = auto()
    SETTINGS = auto()
    AMP = auto()
    FOLLOW_CONFIG = auto()
    EMP = auto()
    EVENT_ARTISTS = auto()
    FOLLOWS = auto()
    ARTIST_EVENT = auto()
    ARTIST_EVENT_START = auto()
    ARTIST_EVENT_END = auto()
    GLOBAL_EVENT = auto()
    GLOBAL_EVENT_START = auto()
    GLOBAL_EVENT_END = auto()
