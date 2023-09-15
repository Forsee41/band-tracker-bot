from telegram import Bot
import os
from band_tracker.notifier import Notifier
import asyncio


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    bot = Bot(token=token)
    notifier = Notifier(
        bot=bot,
        admin_chats=[
            0,
        ],
    )
    asyncio.run(notifier.notify_admins(text="Here's a notification for you :)"))


if __name__ == "__main__":
    main()
