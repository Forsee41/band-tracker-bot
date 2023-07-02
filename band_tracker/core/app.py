from typing import Callable

from telegram.ext import Application, ApplicationBuilder


def build_app(
    token: str, handler_registrator: Callable[[Application], None]
) -> Application:
    """
    Builds an application base and registers common handlers via provided handler
    registrator.
    """
    app = ApplicationBuilder()
    app = app.token(token)
    app = app.build()
    handler_registrator(app)
    return app


def run(app: Application) -> None:
    """
    Registers repeatable tasks and starts an event loop.
    """
    app.run_polling()
