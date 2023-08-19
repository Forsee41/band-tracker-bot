from typing import Callable

from telegram.ext import Application, ApplicationBuilder

from band_tracker.db.dal import BotDAL


def build_app(
    token: str,
    handler_registrator: Callable[[Application], None],
    dal: BotDAL,
) -> Application:
    """
    Builds an application base and registers common handlers via provided handler
    registrator.
    """
    app = ApplicationBuilder()
    app = app.token(token)
    #  possible type related errors are further checked
    app = app.build()  # type: ignore
    handler_registrator(app)  # type: ignore
    _add_dal_di(dal=dal, app=app)
    return app  # type: ignore


def run(app: Application) -> None:
    """
    Registers repeatable tasks and starts an event loop.
    """
    app.run_polling()


def _add_dal_di(dal: BotDAL, app: Application) -> None:
    app.bot_data["dal"] = dal
