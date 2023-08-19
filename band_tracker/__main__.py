import logging

from dotenv import load_dotenv
from telegram.error import InvalidToken

from band_tracker.bot.app import build_app, run
from band_tracker.bot.handlers_registrator import register_handlers
from band_tracker.config.env_loader import load_env_vars
from band_tracker.config.log import load_log_config


def main() -> None:
    load_log_config()
    log = logging.getLogger(__name__)

    load_dotenv()
    try:
        env_vars = load_env_vars()
    except EnvironmentError as e:
        log.critical(e)
        return

    app = build_app(token=env_vars.TG_BOT_TOKEN, handler_registrator=register_handlers)

    try:
        run(app)
    except InvalidToken:
        log.critical("Telegram token was rejected by the server")
        return


if __name__ == "__main__":
    main()
