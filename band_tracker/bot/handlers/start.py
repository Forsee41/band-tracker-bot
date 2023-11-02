import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.user_helper import get_user
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    assert dal

    user_tg = update.effective_user
    if not user_tg:
        log.warning("Start handler can't find an effective user!")
        return

    user = await get_user(tg_user=user_tg, dal=dal)

    if not update.effective_chat:
        log.warning("Start handler can't find an effective chat of an update")
        return

    welcoming_text = f"Welcome {user.name}! Use `/help` command to get started!"
    await dal.add_user(user)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=welcoming_text
    )


handlers = [CommandHandler("start", start)]
