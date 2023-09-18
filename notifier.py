import asyncio

from dotenv import load_dotenv
from telegram import Bot

from band_tracker.config.env_loader import tg_bot_env_vars
from band_tracker.notifier import Notifier


async def main() -> None:
    bot_env = tg_bot_env_vars()
    bot = Bot(token=bot_env.TG_BOT_TOKEN)
    notifier = await Notifier.create(
        bot=bot, admin_chats=[], mq_url="", mq_routing_key="", exchange_name=""
    )
    await notifier.consume()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
