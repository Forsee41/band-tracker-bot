import logging
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import get_callback_data
from band_tracker.bot.helpers.context import BTContext
from band_tracker.core.enums import MessageType
from band_tracker.core.event import Event
from band_tracker.core.user import User

log = logging.getLogger(__name__)


def _get_event_callback_data(query: CallbackQuery | None) -> UUID:
    data = get_callback_data(query=query)

    try:
        event_id = UUID(data)
    except ValueError:
        raise InvalidCallbackData("Invalid UUID")
    return event_id


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    if len(event.artist_ids) == 1:
        artist_btn = InlineKeyboardButton(
            text="Artist", callback_data=f"artist {event.artist_ids[0]}"
        )
    else:
        artist_btn = InlineKeyboardButton(
            text="Artists", callback_data=f"eventartists {event.id} 0"
        )

    layout = [
        [
            artist_btn,
            InlineKeyboardButton(
                text="Buy Tickets", callback_data=f"ticketse {event.id}"
            ),
        ],
        [
            InlineKeyboardButton(text="Back", callback_data="menu"),
        ],
    ]
    markup = InlineKeyboardMarkup(layout)
    return markup


def _event_text(event: Event) -> str:
    text_data = f"<b>{event.title}</b>\n\n"
    if event.venue_city and event.venue_country:
        location = f"{event.venue_city}, {event.venue_country}\n"
        text_data += location
    text_data += event.date.strftime("%Y %B %d")
    return text_data


async def event_main_page(update: Update, ctx: BTContext) -> None:
    user: User = await ctx.user()
    query = update.callback_query
    assert query
    await query.answer()

    try:
        event_id = _get_event_callback_data(query)
    except InvalidCallbackData:
        log.error("Event handler got an invalid callback data")
        return

    event = await ctx.dal.get_event(event_id)
    if not event:
        log.warning("Event handler is trying to get an unexciting event")
        return
    if not event.image:
        log.warning(f"Event {event.id} does not have an image")
        return

    await ctx.msg.send_image(
        text=_event_text(event),
        markup=_event_markup(event),
        user=user,
        image=event.image,
        msg_type=MessageType.EMP,
    )


handlers = [
    CallbackQueryHandler(callback=event_main_page, pattern="event .*"),
]
