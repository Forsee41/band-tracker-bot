import logging
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import get_callback_data
from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.core.event import Event
from band_tracker.core.user import User
from band_tracker.db.dal_bot import BotDAL

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


async def event_main_page(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]

    if not update.effective_user:
        log.warning("Event handler can't find an effective user of an update")
        return
    if not update.effective_chat:
        log.warning("Event handler can't find an effective chat of an update")
        return

    user: User = await get_user(update.effective_user, dal=dal)
    query = update.callback_query
    assert query
    await query.answer()
    try:
        event_id = _get_event_callback_data(query)
    except InvalidCallbackData:
        log.error("Event handler got an invalid callback data")
        return

    event = await dal.get_event(event_id)
    if not event:
        log.warning("Event handler is trying to get an unexisting event")
        return
    if not event.image:
        log.warning(f"Event {event.id} does not have an image")
        return

    await msg.send_image(
        text=_event_text(event),
        markup=_event_markup(event),
        user=user,
        image=event.image,
        msg_type=MessageType.EMP,
    )


handlers = [
    CallbackQueryHandler(callback=event_main_page, pattern="event .*"),
]
