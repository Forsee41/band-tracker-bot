from telegram.ext import Application, ApplicationBuilder

from band_tracker.handlers.registrator import register_handlers


def build_app(token: str) -> Application:
    app = ApplicationBuilder()
    app = app.token(token)
    app = app.build()
    register_handlers(app)
    return app


def run_bot(app: Application) -> None:
    app.run_polling()
