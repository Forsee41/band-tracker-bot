import logging
from uuid import UUID

from band_tracker.core.artist import Artist, ArtistSocials
from band_tracker.core.event import Event, EventSales
from band_tracker.db.models import ArtistDB, ArtistSocialsDB, EventDB, GenreDB, SalesDB
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
