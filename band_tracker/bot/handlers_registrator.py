from telegram.ext import Application, BaseHandler

from band_tracker.bot.handlers import artist, inline_query, query, start, test


def _get_handlers() -> list[BaseHandler]:
    handler_lists: list = [
        query.handlers,
        test.handlers,
        inline_query.handlers,
        artist.handlers,
        start.handlers,
    ]

    result: list[BaseHandler] = []
    for handler_list in handler_lists:
        result += handler_list
    return result


def register_handlers(app: Application) -> None:
    handlers = _get_handlers()
    for handler in handlers:
        app.add_handler(handler)
