import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

from band_tracker.bot.helpers.context import BTContext
from band_tracker.core.enums import MessageType

log = logging.getLogger(__name__)


async def send_menu(update: Update, ctx: BTContext) -> None:
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
    user = await ctx.user()

    query = update.callback_query
    if query:
        await query.answer()

    await ctx.msg.send_text(
        text="Band Tracker Bot Menu",
        markup=markup,
        user=user,
        msg_type=MessageType.MENU,
    )


handlers = [
    CommandHandler("menu", send_menu),
    CallbackQueryHandler(callback=send_menu, pattern="^menu$"),
]
