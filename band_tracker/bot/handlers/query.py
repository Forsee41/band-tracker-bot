import logging

from telegram import Update
from telegram.ext import CommandHandler

from band_tracker.bot.helpers.context import BTContext
from band_tracker.core.enums import MessageType

log = logging.getLogger(__name__)


async def query_artists(update: Update, ctx: BTContext) -> None:
    user = await ctx.user()

    args = ctx.args
    assert args
    query = "".join(args)

    if len(query) > 255:
        query = query[:255]

    result_artists = await ctx.dal.search_artist(query)
    result_artist_names = [artist.name for artist in result_artists]

    if result_artist_names:
        result_str = ", ".join(result_artist_names)
    else:
        result_str = "No artists found!"

    if update.effective_chat:
        await ctx.msg.send_text(
            text=result_str,
            markup=None,
            user=user,
            msg_type=MessageType.TEST,
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")
    assert update.effective_chat


handlers = [CommandHandler("query", query_artists)]
