from telegram.ext import Application, BaseHandler

from band_tracker.bot.handlers import artist, inline_query, query, test


def _get_handlers() -> list[BaseHandler]:
    handler_lists = [
        query.handlers,
        test.handlers,
        inline_query.handlers,
        artist.handlers,
    ]

    result = []
    for handler_list in handler_lists:
        result += handler_list
    return result


def register_handlers(app: Application) -> None:
    handlers = _get_handlers()
    for handler in handlers:
        app.add_handler(handler)
