import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.user_helper import get_user
from band_tracker.core.artist import Artist
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def show_artist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Artist handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Artist handler can't find an effective user of an update")
        return

    user = await get_user(tg_user=update.effective_user, dal=dal)

    args = context.args
    if not args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter an artist name",
        )
        return

    name = " ".join(args)

    if len(name) > 255:
        name = name[:255]

    artist = await dal.get_artist_by_name(name)

    if artist is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Can't find an artist"
        )
        return

    if artist.id in [follow.artist for follow in user.follows]:
        method = _show_followed_amp
    elif artist.id in user.subscriptions:
        method = _show_subscribed_amp
    else:
        method = _show_unsubscribed_amp
    await method(bot=context.bot, chat_id=update.effective_chat.id, artist=artist)


async def _show_unsubscribed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    buttons = [
        InlineKeyboardButton("Subscribe", callback_data=f"subscribe {artist.id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])

    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def _show_subscribed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    buttons = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist.id}"),
        InlineKeyboardButton("Follow", callback_data=f"follow {artist.id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])

    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def _show_followed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    buttons = [
        InlineKeyboardButton("Unsubscribe", callback_data=f"unsubscribe {artist.id}"),
        InlineKeyboardButton("Unfollow", callback_data=f"unfollow {artist.id}"),
    ]
    markup = InlineKeyboardMarkup([buttons])

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


handlers = [CommandHandler("artist", show_artist)]
