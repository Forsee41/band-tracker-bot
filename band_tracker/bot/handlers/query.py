import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.db.dal import BotDAL

log = logging.getLogger(__name__)


async def query_artists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]

    args = context.args
    assert args
    query = "".join(args)

    if len(query) > 255:
        query = query[:255]

    result_artists = await dal.search_artist(query)
    result_artist_names = [artist.name for artist in result_artists]

    if result_artist_names:
        result_str = ", ".join(result_artist_names)
    else:
        result_str = "No artists found!"

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=result_str
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")
    assert update.effective_chat


handlers = [CommandHandler("query", query_artists)]
