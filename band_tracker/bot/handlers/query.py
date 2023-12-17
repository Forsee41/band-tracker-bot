import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.enums import MessageType
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def query_artists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    msg: MessageManager = context.bot_data["msg"]
    assert update.effective_user
    user = await get_user(tg_user=update.effective_user, dal=dal)

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
        await msg.send_text(
            text=result_str,
            markup=None,
            user=user,
            msg_type=MessageType.TEST,
        )
    else:
        log.warning("Test handler can't find an effective chat of an update")
    assert update.effective_chat


handlers = [CommandHandler("query", query_artists)]
