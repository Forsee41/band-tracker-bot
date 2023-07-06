from enum import Enum


class Range(Enum):
    CITY = "CITY"
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    WORLDWIDE = "WORLDWIDE"


class EventType(Enum):
    concert: None
    fest: None
    # remove?


class EventSource(Enum):
    seatgeek_api: None
    ticketmaster_api: None


class TrackingDistance(Enum):
    city: None
    country: None
    region: None
    worldwide: None
