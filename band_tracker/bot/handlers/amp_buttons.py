import logging
from uuid import UUID

from telegram import CallbackQuery, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, InvalidCallbackData

from band_tracker.bot.artist_main_page import subscribed_markup

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


async def subscribe(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    try:
        artist_id = _get_callback_data(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    assert context.bot
    assert query
    assert query.message

    new_markup = subscribed_markup(artist_id=artist_id)
    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=new_markup,
    )


async def follow(update: Update, context: CallbackContext) -> None:
    ...


async def unsubscribe(update: Update, context: CallbackContext) -> None:
    ...


async def unfollow(update: Update, context: CallbackContext) -> None:
    ...


handlers = [
    CallbackQueryHandler(callback=subscribe, pattern="subscribe .*"),
    CallbackQueryHandler(callback=follow, pattern="follow .*"),
    CallbackQueryHandler(callback=unsubscribe, pattern="unsubscribe .*"),
    CallbackQueryHandler(callback=unfollow, pattern="unfollow .*"),
]
