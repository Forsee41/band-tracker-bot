import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

log = logging.getLogger(__name__)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        log.info("Test handler invoked")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Test handler works!"
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")


handlers = [CommandHandler("test", test)]
