import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.core.user import User
from band_tracker.core.user_settings import UserSettings
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    assert dal

    user_tg = update.effective_user
    assert user_tg

    user_settings = UserSettings.default()
    user = User(
        id=int(user_tg.id),
        name=user_tg.name,
        subscriptions=[],
        follows=[],
        join_date=datetime.now(),
        settings=user_settings,
    )
    log.info(f"registered a new user with uuid {user.id}")

    if not update.effective_chat:
        log.warning("Test handler can't find an effective chat of an update")
        return
    welcoming_text = f"Welcome {user.name}! Use `/help` command to get started!"
    await dal.add_user(user)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=welcoming_text
    )


handlers = [CommandHandler("start", start)]
