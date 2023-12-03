import asyncio
import logging
from typing import Awaitable
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

from band_tracker.bot.helpers.callback_data import (
    get_callback_data,
    get_multiple_fields,
)
from band_tracker.config.constants import EVENTS_PER_PAGE
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


def _get_all_events_callback_data(query: CallbackQuery | None) -> int:
    data = get_callback_data(query=query)

    try:
        page_number = int(data)
    except ValueError:
        raise InvalidCallbackData("Invalid UUID")
    return page_number


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    layout = [
        [
            InlineKeyboardButton(text="Explore", callback_data=f"event {event.id}"),
            InlineKeyboardButton(
                text="Buy Tickets", callback_data=f"tickets {event.id}"
            ),
        ],
    ]
    return InlineKeyboardMarkup(layout)


def _events_nav_markup(next_page: bool, page: int = 0) -> InlineKeyboardMarkup:
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="Prev", callback_data=f"eventsall {page-1}")
        )
    if next_page:
        nav_row.append(
            InlineKeyboardButton(text="Next", callback_data=f"eventsall {page+1}")
        )
    back_btn = InlineKeyboardButton(text="Back", callback_data="menu")
    markup = InlineKeyboardMarkup([nav_row, [back_btn]])
    return markup


def _event_text(event: Event) -> str:
    result = f"{event.title}\n\n{event.date.strftime('%Y %B %d')}"
    return result


async def _send_events(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    events: list[Event],
    next_page: bool,
    page: int = 0,
) -> None:
    bot: Bot = context.bot
    if not update.effective_chat:
        log.warning("Can't send events cause can't find an effective chat of an update")
        return
    tasks: list[Awaitable] = []
    for event in events:
        event_text = _event_text(event)
        event_markup = _event_markup(event)
        tasks.append(
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=event_text,
                reply_markup=event_markup,
            )
        )
    nav_markup = _events_nav_markup(next_page=next_page, page=page)
    await asyncio.gather(*tasks)
    await bot.send_message(
        chat_id=update.effective_chat.id, text="Navigation", reply_markup=nav_markup
    )


async def all_events_command(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return

    user_id = update.effective_user.id
    events = await dal.get_events_for_user(user_id, events_per_page=EVENTS_PER_PAGE)
    total_events = await dal.get_user_events_amount(user_id)
    next_page = False
    if (total_events - 1) // EVENTS_PER_PAGE > 0:
        next_page = True
    await _send_events(
        update=update, context=context, events=events, next_page=next_page
    )


async def all_events_btn(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return
    query = update.callback_query
    page = _get_all_events_callback_data(query)
    user_id = update.effective_user.id
    events = await dal.get_events_for_user(
        user_id, events_per_page=EVENTS_PER_PAGE, page=page
    )

    total_events = await dal.get_user_events_amount(user_id)
    next_page = False
    if (total_events - 1) // EVENTS_PER_PAGE > page:
        next_page = True

    await _send_events(
        update=update, context=context, events=events, next_page=next_page, page=page
    )


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
    CommandHandler("events", all_events_command),
    CallbackQueryHandler(callback=artist_events, pattern="^eventsar .*$"),
    CallbackQueryHandler(callback=all_events_btn, pattern="^eventsall .*$"),
]
