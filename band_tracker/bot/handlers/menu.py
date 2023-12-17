import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def send_menu(update: Update, context: CallbackContext) -> None:
    msg: MessageManager = context.bot_data["msg"]
    dal: BotDAL = context.bot_data["dal"]
    assert update.effective_user
    markup_layout = [
        [
            InlineKeyboardButton("Follows", callback_data="follows"),
        ],
        [
            InlineKeyboardButton("Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("Events", callback_data="eventsall 0"),
        ],
        [
            InlineKeyboardButton("Help", callback_data="help"),
        ],
    ]
    markup = InlineKeyboardMarkup(markup_layout)
    user = await get_user(dal=dal, tg_user=update.effective_user)

    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    if query:
        await query.answer()

    await msg.send_text(
        text="Band Tracker Bot Menu",
        markup=markup,
        user=user,
        msg_type=MessageType.MENU,
    )


handlers = [
    CommandHandler("menu", send_menu),
    CallbackQueryHandler(callback=send_menu, pattern="^menu$"),
]
