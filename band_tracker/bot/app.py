from typing import Callable

from telegram.ext import Application, ApplicationBuilder

from band_tracker.db.dal_bot import BotDAL


def build_app(
    token: str,
    handler_registrator: Callable[[Application], None],
    dal: BotDAL,
) -> Application:
    """
    Builds an application base and registers common handlers via provided handler
    registrator.
    """
    builder = ApplicationBuilder()
    builder = builder.token(token)
    app = builder.build()
    handler_registrator(app)
    _inject_app_dependencies(dal=dal, app=app)
    return app


def run(app: Application) -> None:
    """
    Registers repeatable tasks and starts an event loop.
    """
    app.run_polling()


def _inject_app_dependencies(dal: BotDAL, app: Application) -> None:
    app.bot_data["dal"] = dal
