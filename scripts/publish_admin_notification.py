"""
Publishes admin notification to mq.
Example:
    `python scripts/publish_admin_notification.py Message`
"""
import asyncio
import os
import sys


async def main() -> None:
    from dotenv import load_dotenv

    from band_tracker.config.env_loader import mq_env_vars
    from band_tracker.mq_publisher import MessageType, MQPublisher

    load_dotenv()
    mq_env = mq_env_vars()
    publisher = await MQPublisher.create(
        routing_key="notification",
        url=mq_env.MQ_URI,
        exchange=mq_env.MQ_EXCHANGE,
    )

    msg = sys.argv[1] if len(sys.argv) > 1 else None
    if not msg:
        msg = "Here's my message"
    await publisher.send_message(
        data={"message": msg}, type_=MessageType.admin_notification
    )


if __name__ == "__main__":
    sys.path.append(os.getcwd())
    asyncio.run(main())
