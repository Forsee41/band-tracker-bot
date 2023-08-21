import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.db.dal import BotDAL

log = logging.getLogger(__name__)


async def query_artists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    assert args
    query = args[0]
    dal: BotDAL = context.bot_data["dal"]
    result_artists = await dal.search_artist(query)
    result_artist_names = [artist.name for artist in result_artists]
    result_str = ", ".join(result_artist_names)
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=result_str
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")
    assert update.effective_chat


handlers = [CommandHandler("query", query_artists)]
