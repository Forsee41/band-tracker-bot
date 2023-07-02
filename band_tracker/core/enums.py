from enum import Enum


class Genre(Enum):
    rock: None
    indie: None


class EventType(Enum):
    concert: None
    other: None


class EventSource(Enum):
    seatgeek_api: None


class TrackingDistance(Enum):
    city: None
    country: None
    region: None
    worldwide: None
