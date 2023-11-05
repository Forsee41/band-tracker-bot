import logging
from uuid import UUID

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from band_tracker.core.artist import Artist

log = logging.getLogger(__name__)


def unsubscribed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Subscribe", callback_data=f"subscribe {artist_id}"),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"tickets {artist_id}"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


def subscribed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist_id}"),
        InlineKeyboardButton("Follow", callback_data=f"follow {artist_id}"),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"tickets {artist_id}"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


def followed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist_id}"),
        InlineKeyboardButton("Unfollow", callback_data=f"unfollow {artist_id}"),
    ]
    row2 = [
        InlineKeyboardButton(
            "Configure Subscription", callback_data=f"subscription {artist_id}"
        ),
    ]
    row3 = [
        InlineKeyboardButton("Events", callback_data=f"tickets {artist_id}"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2, row3])
    return markup


async def show_unsubscribed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    markup = unsubscribed_markup(artist.id)
    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def show_subscribed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    markup = subscribed_markup(artist.id)

    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def show_followed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    markup = followed_markup(artist.id)
    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def _send_result(
    bot: Bot, chat_id: int, artist: Artist, markup: InlineKeyboardMarkup
) -> None:
    text_data = f"<b>{artist.name}</b>\n\n"
    if artist.genres:
        genres = " ".join(artist.genres)
        genres_str = f"Genres: {genres}\n"
        text_data += genres_str
    if artist.socials.instagram:
        text_data += f'<a href="{artist.socials.instagram}">Instagram</a>\n'
    if artist.socials.youtube:
        text_data += f'<a href="{artist.socials.youtube}">YouTube</a>\n'
    if artist.socials.spotify:
        text_data += f'<a href="{artist.socials.spotify}">Spotify</a>\n'

    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.image,  # type: ignore
        caption=text_data,
        reply_markup=markup,
        parse_mode="HTML",
    )
