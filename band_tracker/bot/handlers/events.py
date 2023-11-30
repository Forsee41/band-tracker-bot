import logging
from uuid import UUID

from telegram import Bot, CallbackQuery, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InvalidCallbackData,
)

from band_tracker.bot.helpers.callback_data import (
    get_callback_data,
    get_multiple_fields,
)
from band_tracker.core.event import Event
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


def _get_artist_events_callback_data(query: CallbackQuery | None) -> tuple[UUID, int]:
    result_fields = get_multiple_fields(query=query)
    total_fields = len(result_fields)

    if total_fields != 3:
        raise InvalidCallbackData(
            f"Callback should have 3 fields, got {total_fields} instead "
        )
    try:
        target_page = int(result_fields[2])
    except ValueError:
        raise InvalidCallbackData("Invalid target page")
    try:
        uuid = UUID(result_fields[1])
    except ValueError:
        raise InvalidCallbackData("Invalid UUID")
    return uuid, target_page


def _get_all_events_callback_data(query: CallbackQuery | None) -> UUID:
    data = get_callback_data(query=query)

    try:
        uuid = UUID(data)
    except ValueError:
        raise InvalidCallbackData("Invalid UUID")
    return uuid


async def _send_events(
    update: Update, context: ContextTypes.DEFAULT_TYPE, events: list[Event]
) -> None:
    bot: Bot = context.bot
    if not update.effective_chat:
        log.warning("Can't send events cause can't find an effective chat of an update")
        return
    for event in events:
        if event.image:
            await bot.send_photo(chat_id=update.effective_chat.id, photo=event.image)
        else:
            await bot.send_message(chat_id=update.effective_chat.id, text="hello")


async def all_events(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return
    query = update.callback_query
    assert dal, query


async def artist_events(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return
    query = update.callback_query
    assert dal, query


handlers = [
    CommandHandler("events", all_events),
    CallbackQueryHandler(callback=artist_events, pattern="^eventsar .*$"),
    CallbackQueryHandler(callback=all_events, pattern="^eventsall .*$"),
]
