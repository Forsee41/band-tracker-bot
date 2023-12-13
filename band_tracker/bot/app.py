from typing import Callable

from telegram.ext import Application, ApplicationBuilder

from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.dal_message import MessageDAL


def build_app(
    token: str,
    handler_registrator: Callable[[Application], None],
    bot_dal: BotDAL,
    msg_dal: MessageDAL,
) -> Application:
    """
    Builds an application base and registers common handlers via provided handler
    registrator.
    """
    builder = ApplicationBuilder()
    builder = builder.token(token)
    app = builder.build()
    handler_registrator(app)
    _inject_app_dependencies(bot_dal=bot_dal, msg_dal=msg_dal, app=app)
    return app


def run(app: Application) -> None:
    """
    Registers repeatable tasks and starts an event loop.
    """
    app.run_polling()


def _inject_app_dependencies(
    bot_dal: BotDAL, msg_dal: MessageDAL, app: Application
) -> None:
    msg_manager = MessageManager(msg_dal=msg_dal, bot=app.bot)
    app.bot_data["dal"] = bot_dal
    app.bot_data["msg"] = msg_manager
