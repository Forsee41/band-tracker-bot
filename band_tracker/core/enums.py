from enum import Enum


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
