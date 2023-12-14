import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]
    assert update.effective_user
    user = await get_user(dal=dal, tg_user=update.effective_user)
    if update.effective_chat:
        log.info("Test handler invoked")
        await msg.send_text(
            text="Test handler works!",
            markup=None,
            user=user,
            msg_type=MessageType.TEST,
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")


handlers = [CommandHandler("test", test)]
