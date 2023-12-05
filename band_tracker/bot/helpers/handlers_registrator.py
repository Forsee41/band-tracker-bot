import importlib
import pkgutil

from telegram.ext import Application, BaseHandler

import band_tracker.bot.handlers


def _get_handlers() -> list[BaseHandler]:
    handlers_path = band_tracker.bot.handlers.__path__
    module_names: list = [name for _, name, _ in pkgutil.iter_modules(handlers_path)]
    pkg_name = "band_tracker.bot.handlers"
    modules: list = [
        importlib.import_module(f"{pkg_name}.{module_name}")
        for module_name in module_names
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
