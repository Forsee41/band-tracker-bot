import asyncio

from dotenv import load_dotenv
from telegram import Bot

from band_tracker.config.env_loader import tg_bot_env_vars
from band_tracker.notifier import Notifier


def main() -> None:
    bot_env = tg_bot_env_vars()
    bot = Bot(token=bot_env.TG_BOT_TOKEN)
    notifier = Notifier(
        bot=bot,
        admin_chats=[
            986579738,
        ],
    )
    asyncio.run(notifier.notify_admins(text="Here's a notification for you :)"))


if __name__ == "__main__":
    load_dotenv()
    main()
