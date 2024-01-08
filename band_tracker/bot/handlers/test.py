import logging

from telegram import Update
from telegram.ext import CommandHandler

from band_tracker.bot.helpers.context import BTContext
from band_tracker.core.enums import MessageType

log = logging.getLogger(__name__)


async def test(update: Update, ctx: BTContext) -> None:
    user = await ctx.user()
    if not update.effective_chat:
        log.warning("Test handler can't find an effective chat of an update")

    log.info("Test handler invoked")
    await ctx.msg.send_text(
        text="Test handler works!",
        markup=None,
        user=user,
        msg_type=MessageType.TEST,
    )


handlers = [CommandHandler("test", test)]
