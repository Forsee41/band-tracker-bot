import logging
from uuid import UUID

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.event import Event, EventSales
from band_tracker.core.follow import Follow
from band_tracker.core.user import User
from band_tracker.core.user_settings import UserSettings
from band_tracker.db.models import (
    ArtistDB,
    ArtistSocialsDB,
    EventDB,
    FollowDB,
    GenreDB,
    SalesDB,
    UserDB,
    UserSettingsDB,
)
from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


class BaseDAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    def _build_core_event(
        self, db_event: EventDB, db_sales: SalesDB, artist_ids: list[UUID]
    ) -> Event:
        sales = EventSales(
            price_min=db_sales.price_min,
            sale_start=db_sales.sale_start,
            sale_end=db_sales.sale_end,
            price_max=db_sales.price_max,
            currency=db_sales.currency,
        )

        event = Event(
            id=db_event.id,
            artist_ids=artist_ids,
            sales=sales,
            title=db_event.title,
            date=db_event.start_date,
            venue=db_event.venue,
            venue_city=db_event.venue_city,
            venue_country=db_event.venue_country,
            ticket_url=db_event.ticket_url,
            image=db_event.image,
        )
        return event

    def _build_core_artist(
        self, db_artist: ArtistDB, db_socials: ArtistSocialsDB, genres: list[GenreDB]
    ) -> Artist:
        socials = ArtistSocials(
            spotify=db_socials.spotify,
            instagram=db_socials.instagram,
            youtube=db_socials.youtube,
        )
        genre_names = [genre.name for genre in genres]

        artist = Artist(
            id=db_artist.id,
            name=db_artist.name,
            tickets_link=db_artist.tickets_link,
            socials=socials,
            image=db_artist.image,
            genres=genre_names,
        )
        return artist

    def _core_to_db_user(self, user: User) -> UserDB:
        db_settings = self._core_to_db_user_settings(user.settings)
        db_user = UserDB(
            tg_id=user.id,
            name=user.name,
            join_date=user.join_date,
            settings=db_settings,
        )
        return db_user

    def _db_to_core_user(self, user_db: UserDB) -> User:
        settings = self._db_to_core_user_settings(user_db.settings)
        follows = [self._db_to_core_follow(follow_db) for follow_db in user_db.follows]
        user = User(
            id=user_db.tg_id,
            name=user_db.name,
            join_date=user_db.join_date,
            settings=settings,
            follows=follows,
        )
        return user

    def _db_to_core_follow(self, follow_db: FollowDB) -> Follow:
        return Follow(artist=str(follow_db.artist.id), locations=None)

    def _core_to_db_user_settings(self, settings: UserSettings) -> UserSettingsDB:
        assert settings
        settings_db = UserSettingsDB(is_muted=False)
        return settings_db

    def _db_to_core_user_settings(self, settings_db: UserSettingsDB) -> UserSettings:
        assert settings_db
        settings = UserSettings.default()
        return settings
