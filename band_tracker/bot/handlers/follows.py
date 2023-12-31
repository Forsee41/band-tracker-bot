import logging
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import get_callback_data
from band_tracker.bot.helpers.context import BTContext
from band_tracker.config.constants import ARTISTS_PER_PAGE
from band_tracker.core.enums import MessageType
from band_tracker.core.user import User
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


def _get_callback_follows_page(query: CallbackQuery | None) -> int:
    result_text = get_callback_data(query=query)
    try:
        target_page = int(result_text)
    except ValueError:
        raise InvalidCallbackData("Invalid target page")
    return target_page


async def _follows_markup(user: User, page: int, dal: BotDAL) -> InlineKeyboardMarkup:
    button_list: list[list[InlineKeyboardButton]] = []
    follows_list = [follow for follow in user.follows.values()]
    follows_list.sort(key=lambda follow: follow.artist)
    if len(follows_list) // ARTISTS_PER_PAGE < page:
        raise ValueError("Not enough follows to fill selected page")

    # substracting 1 from length cause you need at least 1 extra for the next page to
    # contain something
    follows_amount = len(follows_list)
    total_pages = max(0, ((follows_amount - 1) // ARTISTS_PER_PAGE) + 1)
    next_page_exists = total_pages >= (page + 2)
    log.debug(
        f"follows: {len(follows_list)}, {page=}, {next_page_exists=}, {total_pages=}"
    )
    if next_page_exists:
        start_index = ARTISTS_PER_PAGE * page
        target_follows = follows_list[start_index : start_index + ARTISTS_PER_PAGE]
    else:
        target_follows = follows_list[ARTISTS_PER_PAGE * page :]

    names: dict[UUID, str] = await dal.get_artist_names(
        [follow.artist for follow in target_follows]
    )
    for id, name in names.items():
        button = InlineKeyboardButton(text=name, callback_data=f"artist {id}")
        button_list.append([button])

    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="Previous", callback_data=f"follows {page - 1}")
        )
    if next_page_exists:
        nav_row.append(
            InlineKeyboardButton(text="Next", callback_data=f"follows {page + 1}")
        )
    button_list.append(nav_row)
    button_list.append([InlineKeyboardButton(text="Back", callback_data="menu")])

    markup = InlineKeyboardMarkup(button_list)
    return markup


async def follows_command(update: Update, ctx: BTContext) -> None:
    user = await ctx.user()
    markup = await _follows_markup(user=user, page=0, dal=ctx.dal)
    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    if query:
        await query.answer()

    await ctx.msg.send_text(
        text="Your Follows", markup=markup, user=user, msg_type=MessageType.FOLLOWS
    )


async def follows_navigation(update: Update, ctx: BTContext) -> None:
    query = update.callback_query
    try:
        page_number = _get_callback_follows_page(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    user = await ctx.user()
    try:
        markup = await _follows_markup(user=user, page=page_number, dal=ctx.dal)
    except ValueError:
        log.error("User trying to display follows page he couldn't have")
        return
    assert update.effective_chat
    assert update.effective_chat.id

    assert query
    await query.answer()
    await ctx.msg.send_text(
        text="Your Follows", markup=markup, user=user, msg_type=MessageType.FOLLOWS
    )


handlers = [
    CommandHandler("follows", follows_command),
    CallbackQueryHandler(callback=follows_navigation, pattern="^follows .*$"),
    CallbackQueryHandler(callback=follows_command, pattern="^follows$"),
]
