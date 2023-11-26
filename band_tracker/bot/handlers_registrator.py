from telegram.ext import Application, BaseHandler

from band_tracker.bot.handlers import (
    artist,
    config,
    inline_query,
    menu,
    query,
    start,
    test,
)


def _get_handlers() -> list[BaseHandler]:
    modules: list = [
        query,
        test,
        inline_query,
        artist,
        start,
        menu,
        config,
    ]
    handler_lists: list = [module.handlers for module in modules]

    result: list[BaseHandler] = []
    for handler_list in handler_lists:
        result += handler_list
    return result


def register_handlers(app: Application) -> None:
    handlers = _get_handlers()
    for handler in handlers:
        app.add_handler(handler)
