import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]

    user_tg = update.effective_user
    if not user_tg:
        log.warning("Start handler can't find an effective user!")
        return

    user = await get_user(tg_user=user_tg, dal=dal)

    if not update.effective_chat:
        log.warning("Start handler can't find an effective chat of an update")
        return

    welcoming_text = f"Welcome {user.name}! Use `/help` command to get started!"
    await msg.send_text(
        text=welcoming_text,
        markup=None,
        user=user,
        msg_type=MessageType.START,
    )


handlers = [CommandHandler("start", start)]
