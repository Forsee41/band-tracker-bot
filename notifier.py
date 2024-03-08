import asyncio

from dotenv import load_dotenv
from telegram import Bot

from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.config.constants import MQ_ROUTING_KEY, NO_DELETE
from band_tracker.config.env_loader import db_env_vars, mq_env_vars, tg_bot_env_vars
from band_tracker.db.dal_message import MessageDAL
from band_tracker.db.dal_notifier import NotifierDAL
from band_tracker.db.session import AsyncSessionmaker
from band_tracker.mq.notifier import Notifier


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
    notifier_dal = NotifierDAL(db_sessionmaker)
    msg_dal = MessageDAL(db_sessionmaker)
    msg_manager = MessageManager(msg_dal=msg_dal, bot=bot, no_delete=NO_DELETE)
    notifier = await Notifier.create(
        bot=bot,
        dal=notifier_dal,
        mq_url=mq_env.MQ_URI,
        mq_routing_key=MQ_ROUTING_KEY,
        exchange_name=mq_env.MQ_EXCHANGE,
        msg=msg_manager,
    )
    await notifier.consume()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
