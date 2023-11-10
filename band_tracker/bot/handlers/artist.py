import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.bot.helpers.artist_main_page import (
    show_followed_amp,
    show_unfollowed_amp,
)
from band_tracker.bot.helpers.user import get_user
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def show_artist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]

    if not update.effective_chat:
        log.warning("Artist handler can't find an effective chat of an update")
        return
    if not update.effective_user:
        log.warning("Artist handler can't find an effective user of an update")
        return

    user = await get_user(tg_user=update.effective_user, dal=dal)

    args = context.args
    if not args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter an artist name",
        )
        return

    name = " ".join(args)

    if len(name) > 255:
        name = name[:255]

    artist = await dal.get_artist_by_name(name)

    if artist is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Can't find an artist"
        )
        return

    if artist.id in [follow.artist for follow in user.follows]:
        method = show_followed_amp
    else:
        method = show_unfollowed_amp
    await method(bot=context.bot, chat_id=update.effective_chat.id, artist=artist)


handlers = [CommandHandler("artist", show_artist)]
