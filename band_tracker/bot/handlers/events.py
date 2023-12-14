import asyncio
import logging
from typing import Awaitable
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.config.constants import EVENTS_PER_PAGE
from band_tracker.core.artist import Artist
from band_tracker.core.enums import MessageType
from band_tracker.core.event import Event
from band_tracker.core.user import User
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


def _event_layout(event: Event) -> list[list[InlineKeyboardButton]]:
    layout = [
        [
            InlineKeyboardButton(text="Explore", callback_data=f"event {event.id}"),
            InlineKeyboardButton(
                text="Buy Tickets", callback_data=f"tickets {event.id}"
            ),
        ],
    ]
    return layout


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    layout = _event_layout(event)
    return InlineKeyboardMarkup(layout)


def _all_events_nav_markup(
    next_page: bool, event: Event, page: int = 0
) -> InlineKeyboardMarkup:
    nav_row: list[InlineKeyboardButton] = []
    event_layout = _event_layout(event)
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="Prev", callback_data=f"eventsall {page-1}")
        )
    if next_page:
        nav_row.append(
            InlineKeyboardButton(text="Next", callback_data=f"eventsall {page+1}")
        )
    back_btn = InlineKeyboardButton(text="Back", callback_data="menu")
    event_layout.extend([nav_row, [back_btn]])
    markup = InlineKeyboardMarkup(event_layout)
    return markup


def _artist_events_nav_markup(
    next_page: bool, artist_id: UUID, event: Event, page: int = 0
) -> InlineKeyboardMarkup:
    event_layout = _event_layout(event)
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="Prev", callback_data=f"eventsar {artist_id} {page-1}"
            )
        )
    if next_page:
        nav_row.append(
            InlineKeyboardButton(
                text="Next", callback_data=f"eventsar {artist_id} {page+1}"
            )
        )
    back_callback_data = f"artist {artist_id}"
    back_btn = InlineKeyboardButton(text="Back", callback_data=back_callback_data)
    event_layout.extend([nav_row, [back_btn]])
    markup = InlineKeyboardMarkup(event_layout)
    return markup


def _event_text(event: Event) -> str:
    result = f"{event.title}\n\n{event.date.strftime('%Y %B %d')}"
    return result


async def _send_artist_events(
    context: ContextTypes.DEFAULT_TYPE,
    events: list[Event],
    user: User,
    artist: Artist,
    next_page: bool,
    page: int,
) -> None:
    if len(events) >= 2:
        await _send_artist_events_long(
            context=context,
            events=events,
            user=user,
            next_page=next_page,
            page=page,
            artist=artist,
        )
    elif len(events) == 1:
        await _send_artist_events_short(
            context=context,
            event=events[0],
            user=user,
            next_page=next_page,
            page=page,
            artist=artist,
        )


async def _send_artist_events_short(
    context: ContextTypes.DEFAULT_TYPE,
    event: Event,
    user: User,
    next_page: bool,
    artist: Artist,
    page: int,
) -> None:
    msg: MessageManager = context.bot_data["msg"]
    nav_markup = _artist_events_nav_markup(
        event=event, next_page=next_page, page=page, artist_id=artist.id
    )
    text = f"----------- {artist.name} events -----------\nPage {page+1}\n\n"
    text += _event_text(event)
    await msg.send_text(
        text=text,
        user=user,
        markup=nav_markup,
        msg_type=MessageType.GLOBAL_EVENT_END,
    )


async def _send_artist_events_long(
    context: ContextTypes.DEFAULT_TYPE,
    events: list[Event],
    user: User,
    artist: Artist,
    next_page: bool,
    page: int,
) -> None:
    msg: MessageManager = context.bot_data["msg"]

    # head
    head_markup = _event_markup(event=events[0])
    text = f"----------- {artist.name} events -----------\nPage {page+1}\n\n"
    text += _event_text(events[0])
    await msg.send_text(
        text=text,
        user=user,
        markup=head_markup,
        msg_type=MessageType.ARTIST_EVENT_START,
    )

    # body
    tasks: list[Awaitable] = []
    for event in events[1:-1]:
        event_text = _event_text(event)
        event_markup = _event_markup(event)
        tasks.append(
            msg.send_text(
                user=user,
                text=event_text,
                markup=event_markup,
                msg_type=MessageType.ARTIST_EVENT,
                delete_prev=False,
            )
        )
    await asyncio.gather(*tasks)

    # nav
    nav_markup = _artist_events_nav_markup(
        event=events[-1], artist_id=artist.id, next_page=next_page, page=page
    )
    event_text = _event_text(events[-1])
    await msg.send_text(
        text=event_text,
        user=user,
        markup=nav_markup,
        msg_type=MessageType.ARTIST_EVENT_END,
        delete_prev=False,
    )


async def _send_all_events(
    context: ContextTypes.DEFAULT_TYPE,
    events: list[Event],
    user: User,
    next_page: bool,
    page: int,
) -> None:
    if len(events) >= 2:
        await _send_all_events_long(
            context=context, events=events, user=user, next_page=next_page, page=page
        )
    elif len(events) == 1:
        await _send_all_events_short(
            context=context, event=events[0], user=user, next_page=next_page, page=page
        )


async def _send_all_events_short(
    context: ContextTypes.DEFAULT_TYPE,
    event: Event,
    user: User,
    next_page: bool,
    page: int,
) -> None:
    msg: MessageManager = context.bot_data["msg"]
    nav_markup = _all_events_nav_markup(event=event, next_page=next_page, page=page)
    text = f"----------- Tracked events -----------\nPage {page+1}\n\n"
    text += _event_text(event)
    await msg.send_text(
        text=text,
        user=user,
        markup=nav_markup,
        msg_type=MessageType.GLOBAL_EVENT_END,
    )


async def _send_all_events_long(
    context: ContextTypes.DEFAULT_TYPE,
    events: list[Event],
    user: User,
    next_page: bool,
    page: int,
) -> None:
    msg: MessageManager = context.bot_data["msg"]

    # head
    head_markup = _event_markup(event=events[0])
    text = f"----------- Tracked events -----------\nPage {page+1}\n\n"
    text += _event_text(events[0])
    await msg.send_text(
        text=text,
        user=user,
        markup=head_markup,
        msg_type=MessageType.GLOBAL_EVENT_START,
    )

    # middle
    tasks: list[Awaitable] = []
    for event in events[1:-1]:
        event_text = _event_text(event)
        event_markup = _event_markup(event)
        tasks.append(
            msg.send_text(
                user=user,
                text=event_text,
                markup=event_markup,
                msg_type=MessageType.GLOBAL_EVENT,
                delete_prev=False,
            )
        )
    await asyncio.gather(*tasks)

    # nav
    nav_markup = _all_events_nav_markup(
        event=events[-1], next_page=next_page, page=page
    )
    event_text = _event_text(events[-1])
    await msg.send_text(
        text=event_text,
        user=user,
        markup=nav_markup,
        msg_type=MessageType.GLOBAL_EVENT_END,
        delete_prev=False,
    )


async def all_events_command(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return

    user = await get_user(tg_user=update.effective_user, dal=dal)
    events = await dal.get_events_for_user(
        user_tg_id=user.tg_id, events_per_page=EVENTS_PER_PAGE
    )
    total_events = await dal.get_user_events_amount(user.tg_id)
    next_page = False
    if (total_events - 1) // EVENTS_PER_PAGE > 0:
        next_page = True
    await _send_all_events(
        context=context,
        events=events,
        user=user,
        next_page=next_page,
        page=0,
    )


async def all_events_btn(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return
    user = await get_user(tg_user=update.effective_user, dal=dal)
    query = update.callback_query
    page = _get_all_events_callback_data(query)
    events = await dal.get_events_for_user(
        user_tg_id=user.tg_id, events_per_page=EVENTS_PER_PAGE, page=page
    )

    assert query
    await query.answer()
    total_events = await dal.get_user_events_amount(user.tg_id)
    next_page = False
    if (total_events - 1) // EVENTS_PER_PAGE > page:
        next_page = True

    await _send_all_events(
        context=context,
        events=events,
        user=user,
        next_page=next_page,
        page=page,
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
    assert query
    await query.answer()
    artist_id, page = _get_artist_events_callback_data(query)
    user = await get_user(tg_user=update.effective_user, dal=dal)

    total_events = await dal.get_artist_events_amount(artist_id)
    artist = await dal.get_artist(artist_id)
    events = await dal.get_events_for_artist(artist_id=artist_id, page=page)
    if not events:
        log.warning(
            "Trying to watch a page of artist events when there's not enough events"
        )
        return
    next_page = False
    if (total_events - 1) // EVENTS_PER_PAGE > page:
        next_page = True
    await _send_artist_events(
        context=context,
        events=events,
        user=user,
        artist=artist,
        next_page=next_page,
        page=page,
    )


handlers = [
    CommandHandler("events", all_events_command),
    CallbackQueryHandler(callback=artist_events, pattern="^eventsar .*$"),
    CallbackQueryHandler(callback=all_events_btn, pattern="^eventsall .*$"),
]
