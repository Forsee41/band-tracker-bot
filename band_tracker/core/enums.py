from enum import Enum


class Range(Enum):
    CITY = "CITY"
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    WORLDWIDE = "WORLDWIDE"


class EventSource(Enum):
    ticketmaster_api = "ticketmaster_api"


class TrackingDistance(Enum):
    city: None
    country: None
    region: None
    worldwide: None
