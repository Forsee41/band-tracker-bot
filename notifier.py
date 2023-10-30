import asyncio

from dotenv import load_dotenv
from telegram import Bot

from band_tracker.config.env_loader import db_env_vars, mq_env_vars, tg_bot_env_vars
from band_tracker.db.dal_bot import BotDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.notifier import Notifier


async def main() -> None:
    bot_env = tg_bot_env_vars()
    mq_env = mq_env_vars()
    bot = Bot(token=bot_env.TG_BOT_TOKEN)
    db_env = db_env_vars()
    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = BotDAL(db_sessionmaker)
    notifier = await Notifier.create(
        bot=bot,
        dal=dal,
        mq_url=mq_env.MQ_URI,
        mq_routing_key="notification",
        exchange_name=mq_env.MQ_EXCHANGE,
    )
    await notifier.consume()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
