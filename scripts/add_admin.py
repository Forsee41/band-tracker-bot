"""
Adds an admin to database.
Example:
    `python scripts/add_admin.py admin_name chat_id`
"""
import asyncio
import os
import sys

from dotenv import load_dotenv


async def main() -> None:
    from band_tracker.config.env_loader import db_env_vars
    from band_tracker.db.dal_bot import BotDAL
    from band_tracker.db.session import AsyncSessionmaker

    db_env = db_env_vars()
    db_sessionmaker = AsyncSessionmaker(
        login=db_env.DB_LOGIN,
        password=db_env.DB_PASSWORD,
        ip=db_env.DB_IP,
        port=db_env.DB_PORT,
        database=db_env.DB_NAME,
    )
    dal = BotDAL(db_sessionmaker)

    db_env = db_env_vars()
    name, chat_id = sys.argv[1], sys.argv[2]
    await dal.add_admin(name=name, chat_id=chat_id)


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
