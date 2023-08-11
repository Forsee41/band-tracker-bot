from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as EnumDB
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy import text as alchemy_text
from sqlalchemy.dialects.postgresql import UUID as UUID_PG
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from band_tracker.core.enums import Range


class Base(AsyncAttrs, DeclarativeBase):
    """Base ORM class, contains subclasses' metadata"""


class ArtistDB(Base):
    __tablename__ = "artist"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        primary_key=True,
        server_default=alchemy_text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    tickets_link: Mapped[str | None] = mapped_column(String, nullable=True)
    image: Mapped[str | None] = mapped_column(String, nullable=True)

    subscribers: Mapped[list["UserDB"]] = relationship(
        back_populates="subscriptions",
        secondary="subscription",
    )
    follows: Mapped[list["FollowDB"]] = relationship(back_populates="artist")
    aliases: Mapped[list["ArtistAliasDB"]] = relationship(back_populates="artist")
    genres: Mapped[list["GenreDB"]] = relationship(secondary="artist_genre")
    socials: Mapped["ArtistSocialsDB"] = relationship(back_populates="artist")
    events: Mapped[list["EventDB"]] = relationship(
        secondary="event_artist", back_populates="artists"
    )
    tm_data: Mapped["ArtistTMDataDB"] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )


class EventDB(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        primary_key=True,
        server_default=alchemy_text("gen_random_uuid()"),
    )
    venue: Mapped[str] = mapped_column(String, nullable=False)
    venue_city: Mapped[str] = mapped_column(String, nullable=False)
    venue_country: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    ticket_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image: Mapped[str | None] = mapped_column(String, nullable=True)

    tm_data: Mapped["EventTMDataDB"] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    artists: Mapped[list["ArtistDB"]] = relationship(
        secondary="event_artist", back_populates="events"
    )
    sales: Mapped[list["SalesDB"]] = relationship(back_populates="event")

    @property
    def is_finished(self) -> bool:
        return self.start_date <= datetime.now()


class UserDB(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        primary_key=True,
        server_default=alchemy_text("gen_random_uuid()"),
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


class ArtistSocialsDB(Base):
    __tablename__ = "artist_socials"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    instagram: Mapped[str | None] = mapped_column(String, nullable=True)
    spotify: Mapped[str | None] = mapped_column(String, nullable=True)
    youtube: Mapped[str | None] = mapped_column(String, nullable=True)

    artist: Mapped[ArtistDB] = relationship(back_populates="socials")


class GenreDB(Base):
    __tablename__ = "genre"

    id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        primary_key=True,
        server_default=alchemy_text("gen_random_uuid()"),
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


class ArtistTMDataDB(Base):
    __tablename__ = "artist_tm_data"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    id: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    artist: Mapped[ArtistDB] = relationship(back_populates="tm_data")


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


class SalesDB(Base):
    __tablename__ = "sales"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    )

    sale_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sale_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    price_max: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    price_min: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    currency: Mapped[str | None] = mapped_column(String, nullable=True)

    event: Mapped[EventDB] = relationship(back_populates="sales")


class EventTMDataDB(Base):
    __tablename__ = "event_tm_data"

    event_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    )
    id: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    event: Mapped[EventDB] = relationship(back_populates="tm_data")


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


class ArtistAliasDB(Base):
    __tablename__ = "artist_alias"

    artist_id: Mapped[UUID] = mapped_column(
        UUID_PG(as_uuid=True),
        ForeignKey("artist.id", ondelete="CASCADE"),
    )
    alias: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    artist: Mapped[ArtistDB] = relationship(back_populates="aliases")


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
