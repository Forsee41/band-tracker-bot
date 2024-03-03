import logging
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import (
    get_callback_data,
    get_multiple_fields,
)
from band_tracker.bot.helpers.context import BTContext
from band_tracker.config.constants import EVENTS_PER_PAGE, FRAME, INDENTATION
from band_tracker.core.enums import MessageType
from band_tracker.core.event import Event

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
            InlineKeyboardButton(text="Buy Tickets", url=event.ticket_url),
        ],
    ]
    return layout


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    layout = _event_layout(event)
    return InlineKeyboardMarkup(layout)


def _event_text(event: Event) -> str:
    city = event.venue_city
    country = event.venue_country
    on_sale = event.on_sale

    result = f"{INDENTATION}\n{event.title}\n\n"
    result += f"Location: <b>{city}</b>, <b>{country}</b>\n"
    result += f"Date: <b>{event.date.strftime('%Y %B %d')}</b>\n\n"
    if on_sale:
        result += f"❗️ <b>ON SALE</b> ❗️"

    return result


async def send_artist_events(update: Update, ctx: BTContext) -> None:
    query = update.callback_query

    assert query
    await query.answer()

    total_events = ctx.user_data.get("current_events")
    total_pages = (len(total_events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE

    _, page = _get_artist_events_callback_data(query)

    next_page = False
    if (len(total_events) - 1) // EVENTS_PER_PAGE > page:
        next_page = True

    events = total_events[page * EVENTS_PER_PAGE : (page + 1) * EVENTS_PER_PAGE]

    await _send_events(
        ctx=ctx, next_page=next_page, events=events, page=page, total_pages=total_pages
    )


async def _send_events(
    ctx: BTContext,
    events: list[Event],
    next_page: bool,
    page: int,
    total_pages: int,
    all_events: bool = False,
) -> None:
    user = await ctx.user()

    if all_events:
        left_button = InlineKeyboardButton(
            text="«", callback_data=f"eventsallnav {page - 1}"
        )
        right_button = InlineKeyboardButton(
            text="»", callback_data=f"eventsallnav {page + 1}"
        )
        back_button = InlineKeyboardButton(text="Back", callback_data="menu")
    else:
        artist = ctx.user_data.get("current_artist")
        left_button = InlineKeyboardButton(
            text="«", callback_data=f"eventsnav {artist.id} {page - 1}"
        )
        right_button = InlineKeyboardButton(
            text="»", callback_data=f"eventsnav {artist.id} {page + 1}"
        )
        back_button = InlineKeyboardButton(
            text="Back", callback_data=f"artist {artist.id}"
        )

    first_event = events[0]
    first_event_text = _event_text(first_event)
    first_event_markup = _event_markup(first_event)
    await ctx.msg.send_text(
        user=user,
        text=first_event_text,
        markup=first_event_markup,
        msg_type=MessageType.ARTIST_EVENT,
        delete_prev=True,
    )
    for event in events[1:]:
        event_text = _event_text(event)
        event_markup = _event_markup(event)
        await ctx.msg.send_text(
            user=user,
            text=event_text,
            markup=event_markup,
            msg_type=MessageType.ARTIST_EVENT,
            delete_prev=False,
        )

    # nav
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(left_button)
    if next_page:
        nav_row.append(right_button)

    nav_markup = InlineKeyboardMarkup([nav_row, [back_button]])
    nav_bar_text = f"{FRAME}\n\nPage <b>{page + 1}</b> of {total_pages}\n\n"

    await ctx.msg.send_text(
        text=nav_bar_text,
        user=user,
        markup=nav_markup,
        msg_type=MessageType.ARTIST_EVENT_END,
        delete_prev=False,
    )


async def all_events_gateway(update: Update, ctx: BTContext) -> None:
    user = await ctx.user()
    total_events = await ctx.dal.get_all_events_for_user(user.tg_id)
    if not total_events:
        text = f"----------- there is no upcoming events for you yet :(\n\n"
        event_layout = [[InlineKeyboardButton(text="Back", callback_data="menu")]]
        markup = InlineKeyboardMarkup(event_layout)

        await ctx.msg.send_text(
            text=text,
            user=user,
            markup=markup,
            msg_type=MessageType.GLOBAL_EVENT_END,  # TODO: another mgs_type
        )
        return

    ctx.user_data["current_events"] = total_events

    await send_all_events(update, ctx)


async def send_all_events(update: Update, ctx: BTContext) -> None:
    query = update.callback_query

    if query:
        await query.answer()
        page = _get_all_events_callback_data(query)
    else:
        page = 0

    total_events = ctx.user_data.get("current_events")
    total_pages = (len(total_events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE

    next_page = False
    if (len(total_events) - 1) // EVENTS_PER_PAGE > page:
        next_page = True

    events = total_events[page * EVENTS_PER_PAGE : (page + 1) * EVENTS_PER_PAGE]

    await _send_events(
        ctx=ctx,
        next_page=next_page,
        events=events,
        page=page,
        total_pages=total_pages,
        all_events=True,
    )


async def artist_events_gateway(update: Update, ctx: BTContext) -> None:
    query = update.callback_query
    assert query
    await query.answer()

    artist_id, _ = _get_artist_events_callback_data(query)

    total_events = await ctx.dal.get_all_events_for_artist(artist_id)
    artist = await ctx.dal.get_artist(artist_id)
    if not total_events:
        text = f"----------- {artist.name} has no upcoming events\n\n"
        user = await ctx.user()
        event_layout = [
            [InlineKeyboardButton(text="Back", callback_data=f"artist {artist.id}")]
        ]
        markup = InlineKeyboardMarkup(event_layout)

        await ctx.msg.send_text(
            text=text,
            user=user,
            markup=markup,
            msg_type=MessageType.GLOBAL_EVENT_END,  # TODO: another mgs_type
        )
        return

    if artist is None:
        log.error(f"Artist events handler can't find an artist {artist_id}")
        return

    ctx.user_data["current_events"] = total_events
    ctx.user_data["current_artist"] = artist

    await send_artist_events(update, ctx)


handlers = [
    CommandHandler("events", all_events_gateway),
    CallbackQueryHandler(callback=artist_events_gateway, pattern="^eventsar .*$"),
    CallbackQueryHandler(callback=send_artist_events, pattern="^eventsnav .*$"),
    CallbackQueryHandler(callback=all_events_gateway, pattern="^eventsall .*$"),
    CallbackQueryHandler(callback=send_all_events, pattern="^eventsallnav .*$"),
]
