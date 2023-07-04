from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as EnumDB
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class ArtistDB(Base):
    __tablename__ = "Artist"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    spotify: Mapped[str] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)
    upcoming_events_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=True)

    subscribers: Mapped[list["UserDB"]]  # TODO
    followers: Mapped[list["FollowDB"]]  # TODO
    genres: Mapped[list["GenreDB"]]  # TODO
    events: Mapped[list["EventDB"]]  # TODO
    sg_data: Mapped["ArtistSGDataDB"]  # TODO


class EventDB:
    __tablename__ = "Event"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    venue: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True)
    type_: Mapped[str] = mapped_column(String, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)

    sg_data: Mapped["EventSGDataDB"]  # TODO
    artists: Mapped[list[ArtistDB]]  # TODO
    stats: Mapped["EventStatsDB"]  # TODO

    @property
    def is_finished(self) -> bool:
        return self.date <= datetime.now()


class UserDB:
    __tablename__ = "User"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    join_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now()
    )

    subscriptions: Mapped[list[ArtistDB]]  # TODO
    follows: Mapped[list["FollowDB"]]  # TODO
    settings: Mapped["UserSettingsDB"]  # TODO


class GenreDB:
    __tablename__ = "Genre"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)


class ArtistGenreDB:
    __tablename__ = "ArtistGenre"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Artist.id"), primary_key=True
    )
    genre_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Genre.id"), primary_key=True
    )

    artist: Mapped[ArtistDB]  # TODO
    genre: Mapped[GenreDB]  # TODO


class ArtistSGDataDB:
    __tablename__ = "ArtistSGData"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Artist.id"), primary_key=True
    )
    slug: Mapped[str] = mapped_column(String, nullable=True)
    id: Mapped[str] = mapped_column(String, nullable=False)

    artist: Mapped[ArtistDB]  # TODO


class EventArtistDB:
    __tablename__ = "EventArtist"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Artist.id"), primary_key=True
    )
    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Event.id"), primary_key=True
    )

    event: Mapped[EventDB]  # TODO
    artist: Mapped[ArtistDB]  # TODO


class EventStatsDB:
    __tablename__ = "EventStats"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Event.id"), primary_key=True
    )
    listing_cnt: Mapped[int] = mapped_column(Integer, nullable=False)
    price_avg: Mapped[int] = mapped_column(Integer, nullable=False)
    price_max: Mapped[int] = mapped_column(Integer, nullable=False)
    price_min: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped[EventDB]  # TODO


class EventSGDataDB:
    __tablename__ = "EventSGData"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Event.id"), primary_key=True
    )
    slug: Mapped[str] = mapped_column(String, nullable=True)
    id: Mapped[str] = mapped_column(String, nullable=False)

    event: Mapped[EventDB]  # TODO


class UserSettingsDB:
    __tablename__ = "UserSettings"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("User.id"), primary_key=True
    )
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[UserDB]  # TODO


class SubscriptionDB:
    __tablename__ = "Subscription"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("User.id"), primary_key=True
    )
    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Artist.id"), primary_key=True
    )

    user: Mapped[UserDB]  # TODO
    artist: Mapped[ArtistDB]  # TODO


class Range(Enum):
    CITY = "CITY"
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    WORLDWIDE = "WORLDWIDE"


class FollowDB:
    __tablename__ = "Follow"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("User.id"), primary_key=True
    )
    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), ForeignKey("Artist.id"), primary_key=True
    )
    range_: Mapped[Range] = mapped_column(
        EnumDB, nullable=False, default=Range.WORLDWIDE
    ).label(
        "range"
    )  # pyright: ignore

    user: Mapped[UserDB]  # TODO
    artist: Mapped[ArtistDB]  # TODO
