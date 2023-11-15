import logging
from typing import Callable
from uuid import UUID

from telegram import (
    Bot,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
)

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.core.artist import Artist
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.errors import ArtistNotFound, UserNotFound

log = logging.getLogger(__name__)


def _unfollowed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Follow", callback_data=f"follow {artist_id}"),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"events {artist_id}"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


def _followed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Unfollow", callback_data=f"unfollow {artist_id}"),
        InlineKeyboardButton(
            "Configure notifications", callback_data=f"notifications {artist_id}"
        ),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"events {artist_id}"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


async def _show_unfollowed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    markup = _unfollowed_markup(artist.id)

    await _send_result(bot=bot, chat_id=chat_id, artist=artist, markup=markup)


async def _show_followed_amp(bot: Bot, chat_id: int, artist: Artist) -> None:
    markup = _followed_markup(artist.id)
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


async def _add_follow(dal: BotDAL, user_id: int, artist_id: UUID) -> None:
    try:
        await dal.add_follow(user_tg_id=user_id, artist_id=artist_id)
    except ArtistNotFound:
        log.warning("Can't create a follow, artist is not present in db")
    except UserNotFound:
        log.warning("Can't create a follow, user is not present in db")


def _get_callback_data(query: CallbackQuery | None) -> UUID:
    if query is None:
        raise InvalidCallbackData(
            "Subscribe button callback handler can't find callback query"
        )
    if query.data is None:
        raise InvalidCallbackData(
            "Subscribe button callback handler can't find callback query data"
        )
    data_parts = query.data.split()
    if len(data_parts) != 2:
        raise InvalidCallbackData(
            "Subscribe button callback handler got invalid callback data,"
            f" {query.data}"
        )
    try:
        artist_id = UUID(data_parts[1])
    except ValueError:
        raise InvalidCallbackData("Invalid artist id")
    return artist_id


async def _change_markup(
    update: Update,
    context: CallbackContext,
    markup_generator: Callable[[UUID], InlineKeyboardMarkup],
    artist_id: UUID,
) -> None:
    query = update.callback_query

    assert context.bot
    assert query
    assert query.message

    await query.answer()
    new_markup = markup_generator(artist_id)
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=new_markup,
    )


async def follow(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]
    query = update.callback_query
    try:
        artist_id = _get_callback_data(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    assert update.effective_user
    user = await get_user(dal=dal, tg_user=update.effective_user)
    await _add_follow(dal=dal, user_id=user.id, artist_id=artist_id)
    await _change_markup(
        update=update,
        context=context,
        markup_generator=_followed_markup,
        artist_id=artist_id,
    )


async def unfollow(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]
    query = update.callback_query
    try:
        artist_id = _get_callback_data(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    assert update.effective_user
    user = await get_user(dal=dal, tg_user=update.effective_user)
    await dal.unfollow(user_tg_id=user.id, artist_id=artist_id)
    await _change_markup(
        update=update,
        context=context,
        markup_generator=_unfollowed_markup,
        artist_id=artist_id,
    )


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

    if artist.id in user.follows:
        send_amp = _show_followed_amp
    else:
        send_amp = _show_unfollowed_amp
    await send_amp(bot=context.bot, chat_id=update.effective_chat.id, artist=artist)


handlers = [
    CommandHandler("artist", show_artist),
    CallbackQueryHandler(callback=follow, pattern="follow .*"),
    CallbackQueryHandler(callback=unfollow, pattern="unfollow .*"),
]
