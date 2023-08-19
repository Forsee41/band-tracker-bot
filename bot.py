import logging

from dotenv import load_dotenv
from telegram.error import InvalidToken

from band_tracker.bot.app import build_app, run
from band_tracker.bot.handlers_registrator import register_handlers
from band_tracker.config.env_loader import db_env_vars, tg_bot_env_vars
from band_tracker.config.log import load_log_config
from band_tracker.db.dal import BotDAL
from band_tracker.db.session import AsyncSessionmaker


def main() -> None:
    load_log_config()
    log = logging.getLogger(__name__)

    load_dotenv()
    try:
        env_vars = tg_bot_env_vars()
    except EnvironmentError as e:
        log.critical(e)
        return

    db_env = db_env_vars()
    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = BotDAL(db_sessionmaker)
    app = build_app(
        token=env_vars.TG_BOT_TOKEN, handler_registrator=register_handlers, dal=dal
    )

    try:
        run(app)
    except InvalidToken:
        log.critical("Telegram token was rejected by the server")
        return


if __name__ == "__main__":
    main()
