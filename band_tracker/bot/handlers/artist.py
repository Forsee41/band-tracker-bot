import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


async def show_artist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dal: BotDAL = context.bot_data["dal"]
    if not update.effective_chat:
        log.warning("Artist handler can't find an effective chat of an update")
        return

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
    buttons = [
        InlineKeyboardButton("Subscribe", callback_data="subscribe"),
        InlineKeyboardButton("Follow", callback_data="follow"),
    ]
    markup = InlineKeyboardMarkup([buttons, buttons])

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=artist.image,  # type: ignore
        caption="Text data",
        reply_markup=markup,
    )


handlers = [CommandHandler("artist", show_artist)]
