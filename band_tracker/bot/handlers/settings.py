import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def _generate_markup(dal: BotDAL, user_tg_id: int) -> InlineKeyboardMarkup:
    assert user_tg_id
    assert dal
    markup_layout = [
        [
            InlineKeyboardButton("Set range", callback_data="settings set_range"),
        ],
        [
            InlineKeyboardButton(
                "Disable notifications", callback_data="settings disable_notifications"
            ),
        ],
        [
            InlineKeyboardButton("Back", callback_data="menu"),
        ],
    ]
    markup = InlineKeyboardMarkup(markup_layout)
    return markup


async def show_settings(update: Update, context: CallbackContext) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]
    tg_user = update.effective_user
    assert tg_user
    user = await get_user(tg_user=tg_user, dal=dal)
    markup = await _generate_markup(dal=dal, user_tg_id=user.tg_id)

    assert update.effective_chat
    assert update.effective_chat.id

    query = update.callback_query
    if query:
        await query.answer()

    await msg.send_text(
        text="Settings", markup=markup, user=user, msg_type=MessageType.SETTINGS
    )


handlers = [
    CommandHandler("settings", show_settings),
    CallbackQueryHandler(callback=show_settings, pattern="^settings$"),
]
