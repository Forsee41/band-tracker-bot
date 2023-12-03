import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

log = logging.getLogger(__name__)


async def send_menu(update: Update, context: CallbackContext) -> None:
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

    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    if query:
        await query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Band Tracker Bot Menu",
        reply_markup=markup,
    )


handlers = [
    CommandHandler("menu", send_menu),
    CallbackQueryHandler(callback=send_menu, pattern="^menu$"),
]
