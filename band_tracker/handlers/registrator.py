from telegram.ext import Application, CommandHandler

from band_tracker.handlers import test


def _get_handlers() -> list[CommandHandler]:
    handler_lists = [
        test.handlers,
    ]

    result = []
    for handler_list in handler_lists:
        result += handler_list
    return result


def register_handlers(app: Application) -> None:
    handlers = _get_handlers()
    for handler in handlers:
        app.add_handler(handler)
