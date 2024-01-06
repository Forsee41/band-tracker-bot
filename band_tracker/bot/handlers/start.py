import logging

from telegram import Update
from telegram.ext import CommandHandler

from band_tracker.bot.helpers.context import BTContext
from band_tracker.core.enums import MessageType

log = logging.getLogger(__name__)


async def start(_: Update, ctx: BTContext) -> None:
    user = await ctx.user()

    welcoming_text = f"Welcome {user.name}! Use `/help` command to get started!"
    await ctx.msg.send_text(
        text=welcoming_text,
        markup=None,
        user=user,
        msg_type=MessageType.START,
    )


handlers = [CommandHandler("start", start)]
