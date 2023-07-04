from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as EnumDB
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from band_tracker.core.enums import Range


class Base(DeclarativeBase):
    """Base ORM class, contains subclasses' metadata"""


class ArtistDB(Base):
    __tablename__ = "artist"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    spotify: Mapped[str] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)
    upcoming_events_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=True)

    subscribers: Mapped[list["UserDB"]] = relationship(
        back_populates="subscriptions",
        secondary="subscription",
    )
    follows: Mapped[list["FollowDB"]] = relationship(back_populates="artist")
    genres: Mapped[list["GenreDB"]] = relationship(secondary="artist_genre")
    events: Mapped[list["EventDB"]] = relationship(
        secondary="event_artist", back_populates="artists"
    )
    sg_data: Mapped["ArtistSGDataDB"] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )


class EventDB(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    venue: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True)
    type_: Mapped[str] = mapped_column("type", String, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)

    sg_data: Mapped["EventSGDataDB"] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    artists: Mapped[list["ArtistDB"]] = relationship(
        secondary="event_artist", back_populates="events"
    )
    stats: Mapped["EventStatsDB"] = relationship(back_populates="event")

    @property
    def is_finished(self) -> bool:
        return self.date <= datetime.now()


class UserDB(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    join_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now()
    )

    subscriptions: Mapped[list["ArtistDB"]] = relationship(
        back_populates="subscribers", secondary="subscription"
    )
    follows: Mapped[list["FollowDB"]] = relationship(back_populates="user")
    settings: Mapped["UserSettingsDB"] = relationship(back_populates="user")


class GenreDB(Base):
    __tablename__ = "genre"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True), primary_key=True, default=uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)


class ArtistGenreDB(Base):
    __tablename__ = "artist_genre"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genre_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("genre.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ArtistSGDataDB(Base):
    __tablename__ = "artist_sg_data"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(String, nullable=True)
    id: Mapped[str] = mapped_column(String, nullable=False)

    artist: Mapped[ArtistDB] = relationship(back_populates="sg_data")


class EventArtistDB(Base):
    __tablename__ = "event_artist"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    )


class EventStatsDB(Base):
    __tablename__ = "event_stats"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    )
    listing_cnt: Mapped[int] = mapped_column(Integer, nullable=False)
    price_avg: Mapped[int] = mapped_column(Integer, nullable=False)
    price_max: Mapped[int] = mapped_column(Integer, nullable=False)
    price_min: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped[EventDB] = relationship(back_populates="stats")


class EventSGDataDB(Base):
    __tablename__ = "event_sg_data"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(String, nullable=True)
    id: Mapped[str] = mapped_column(String, nullable=False)

    event: Mapped[EventDB] = relationship(back_populates="sg_data")


class UserSettingsDB(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[UserDB] = relationship(back_populates="settings")


class SubscriptionDB(Base):
    __tablename__ = "subscription"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )


class FollowDB(Base):
    __tablename__ = "follow"

    user_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    range_: Mapped[Range] = mapped_column(
        "range", EnumDB(Range), nullable=False, default=Range.WORLDWIDE
    )

    user: Mapped[UserDB] = relationship(back_populates="follows")
    artist: Mapped[ArtistDB] = relationship(back_populates="follows")
