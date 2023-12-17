import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


def _back_markup() -> InlineKeyboardMarkup:
    layout = [[InlineKeyboardButton(text="Back", callback_data="helpback")]]
    return InlineKeyboardMarkup(layout)


def _help_markup() -> InlineKeyboardMarkup:
    markup_layout = [
        [
            InlineKeyboardButton("How it works", callback_data="help_howitworks"),
        ],
        [
            InlineKeyboardButton("Commands", callback_data="help_commands"),
        ],
        [
            InlineKeyboardButton(
                "How to search artists", callback_data="help_artistsearch"
            ),
        ],
        [
            InlineKeyboardButton(
                "How to manage follows", callback_data="help_managefollows"
            ),
        ],
        [
            InlineKeyboardButton("Back", callback_data="menu"),
        ],
    ]
    markup = InlineKeyboardMarkup(markup_layout)
    return markup


async def _show_help_answer(update: Update, text: str) -> None:
    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    assert query
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=_back_markup())


async def show_help(update: Update, context: CallbackContext) -> None:
    msg: MessageManager = context.bot_data["msg"]
    dal: BotDAL = context.bot_data["dal"]
    assert update.effective_chat
    assert update.effective_chat.id
    assert update.effective_user

    query = update.callback_query
    if query:
        await query.answer()

    user = await get_user(dal=dal, tg_user=update.effective_user)
    markup = _help_markup()
    await msg.send_text(
        text="Q&A. Choose a question.",
        markup=markup,
        user=user,
        msg_type=MessageType.HELP,
    )


async def back_to_help(update: Update, _: CallbackContext) -> None:
    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    assert query
    await query.answer()

    markup = _help_markup()
    await query.edit_message_text(text="Q&A. Choose a question.", reply_markup=markup)


async def how_it_works(update: Update, _: CallbackContext) -> None:
    text = "Choose an artist via inline query. Follow an artist if you want. Profit."
    await _show_help_answer(update=update, text=text)


async def artist_search(update: Update, _: CallbackContext) -> None:
    text = (
        "You can search artists via an inline query. Type `@band_tracker artist name` "
        "and you'll get suggestions as you type. You can also use "
        "`/artist Artist Name` if you know an exact artist name."
    )
    await _show_help_answer(update=update, text=text)


async def commands(update: Update, _: CallbackContext) -> None:
    text = "Perhaps there should be a bunch of buttons for each command."
    await _show_help_answer(update=update, text=text)


async def manage_follows(update: Update, _: CallbackContext) -> None:
    text = "Not yet implemented."
    await _show_help_answer(update=update, text=text)


handlers = [
    CommandHandler("help", show_help),
    CallbackQueryHandler(callback=show_help, pattern="^help$"),
    CallbackQueryHandler(callback=back_to_help, pattern="^helpback$"),
    CallbackQueryHandler(callback=how_it_works, pattern="^help_howitworks$"),
    CallbackQueryHandler(callback=artist_search, pattern="^help_artistsearch$"),
    CallbackQueryHandler(callback=commands, pattern="^help_commands$"),
    CallbackQueryHandler(callback=manage_follows, pattern="^help_managefollows$"),
]
