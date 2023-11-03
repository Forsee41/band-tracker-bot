import logging
from uuid import UUID

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from band_tracker.core.artist import Artist

log = logging.getLogger(__name__)


def unsubscribed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton("Subscribe", callback_data=f"subscribe {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])
    return markup


def subscribed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist_id}"),
        InlineKeyboardButton("Follow", callback_data=f"follow {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])
    return markup


def followed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist_id}"),
        InlineKeyboardButton("Unfollow", callback_data=f"unfollow {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])
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
    text_data = f"<b>{artist.name}</b>\n"
    if artist.genres:
        genres = " ".join(artist.genres)
        genres_str = f"Genres: {genres}\n"
        text_data += genres_str
    if artist.socials.instagram:
        text_data += f"[Instagram]({artist.socials.instagram})\n"
    if artist.socials.youtube:
        text_data += f"[Youtube]({artist.socials.youtube})\n"
    if artist.socials.spotify:
        text_data += f"[Spotify]({artist.socials.spotify})\n"

    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.image,  # type: ignore
        caption="Text data",
        reply_markup=markup,
        parse_mode="HTML",
    )
