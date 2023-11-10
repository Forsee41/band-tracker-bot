import logging
from typing import Callable
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, InvalidCallbackData

from band_tracker.bot.helpers.artist_main_page import followed_markup, unfollowed_markup
from band_tracker.bot.helpers.follow import add_follow
from band_tracker.bot.helpers.user import get_user
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


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
    await add_follow(dal=dal, user_id=user.id, artist_id=artist_id)
    await _change_markup(
        update=update,
        context=context,
        markup_generator=followed_markup,
        artist_id=artist_id,
    )


async def unfollow(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    try:
        artist_id = _get_callback_data(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    await _change_markup(
        update=update,
        context=context,
        markup_generator=unfollowed_markup,
        artist_id=artist_id,
    )


handlers = [
    CallbackQueryHandler(callback=follow, pattern="follow .*"),
    CallbackQueryHandler(callback=unfollow, pattern="unfollow .*"),
]
