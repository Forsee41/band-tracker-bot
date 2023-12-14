import logging
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import get_multiple_fields
from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.config.constants import ARTISTS_PER_PAGE
from band_tracker.core.enums import MessageType
from band_tracker.core.event import Event
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


def _get_event_artitsts_callback_data(query: CallbackQuery | None) -> tuple[UUID, int]:
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


async def _event_artists_markup(
    event: Event, page: int, dal: BotDAL
) -> InlineKeyboardMarkup:
    button_list: list[list[InlineKeyboardButton]] = []
    artist_list = event.artist_ids
    artist_list.sort(key=lambda id: id)
    if len(artist_list) // ARTISTS_PER_PAGE < page:
        raise ValueError("Not enough follows to fill selected page")

    # substracting 1 from length cause you need at least 1 extra for the next page to
    # contain something
    artists_amount = len(artist_list)
    total_pages = max(0, ((artists_amount - 1) // ARTISTS_PER_PAGE) + 1)
    next_page_exists = total_pages >= (page + 2)
    log.debug(
        f"artists: {len(artist_list)}, {page=}, {next_page_exists=}, {total_pages=}"
    )
    if next_page_exists:
        start_index = ARTISTS_PER_PAGE * page
        target_artists = artist_list[start_index : start_index + ARTISTS_PER_PAGE]
    else:
        target_artists = artist_list[ARTISTS_PER_PAGE * page :]

    names: dict[UUID, str] = await dal.get_artist_names(target_artists)
    for id, name in names.items():
        button = InlineKeyboardButton(text=name, callback_data=f"artist {id}")
        button_list.append([button])

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="Previous", callback_data=f"eventartists {page - 1}"
            )
        )
    if next_page_exists:
        nav_row.append(
            InlineKeyboardButton(text="Next", callback_data=f"eventartists {page + 1}")
        )
    button_list.append(nav_row)
    button_list.append(
        [InlineKeyboardButton(text="Back", callback_data=f"event {event.id}")]
    )

    markup = InlineKeyboardMarkup(button_list)
    return markup


async def artist_list(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]

    if not update.effective_chat:
        log.warning("Follows handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Follows handler can't find an effective user of an update")
        return
    user = await get_user(tg_user=update.effective_user, dal=dal)
    query = update.callback_query
    try:
        event_id, page = _get_event_artitsts_callback_data(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return
    event = await dal.get_event(event_id)
    if event is None:
        log.warning("Artist list handler trying to get an unexisting event")
        return

    try:
        markup = await _event_artists_markup(event=event, page=page, dal=dal)
    except ValueError:
        log.error("User trying to display follows page he couldn't have")
        return
    assert update.effective_chat
    assert update.effective_chat.id

    assert query
    await query.answer()
    text = f"{event.title} artists"
    await msg.send_text(
        text=text, markup=markup, user=user, msg_type=MessageType.EVENT_ARTISTS
    )


handlers = [
    CallbackQueryHandler(callback=artist_list, pattern="^eventartists .*$"),
]
