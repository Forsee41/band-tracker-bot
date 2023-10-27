import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes, InlineQueryHandler

from band_tracker.db.dal import BotDAL

log = logging.getLogger(__name__)


async def handle_inline_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    dal: BotDAL = context.bot_data["dal"]

    log.debug("In inline query handler")

    if not update.inline_query:
        return

    query_raw = update.inline_query.query
    query = " ".join(query_raw.split()[1:])
    result_artists = await dal.search_artist(query)

    log.debug(f"Result artists amount: {len(result_artists)}")

    inline_results: list[InlineQueryResultArticle] = []
    id = 0
    for artist in result_artists:
        thumbnail = artist.image if artist.image else "https://i.imgur.com/u8XHujc.jpeg"
        query_result = InlineQueryResultArticle(
            id=str(id),
            title=artist.name,
            description=str(artist.genres if artist.genres else "No genres"),
            thumbnail_url=thumbnail,
            input_message_content=InputTextMessageContent(artist.name),
        )
        inline_results.append(query_result)
        id += 1
    await update.inline_query.answer(inline_results)


pattern = "^/find*"
handlers = [InlineQueryHandler(callback=handle_inline_query)]
