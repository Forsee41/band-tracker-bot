"""
Adds an admin to database.
Example:
    `python scripts/add_admin.py admin_name chat_id`
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from random import randint

from dotenv import load_dotenv


class TestPredictorDAL:
    async def get_event_amounts(self) -> list[tuple[datetime, int]]:
        data = []
        start_date = datetime.now()
        date = start_date
        for _ in range(1000):
            date += timedelta(days=1)
            item = (date, randint(100, 1200))
            data.append(item)
        result = data
        return result


async def main() -> None:
    from band_tracker.updater.timestamp_predictor import CurrentDataPredictor

    dal = TestPredictorDAL()
    max_date = datetime.now() + timedelta(days=365 * 3)
    predictor = CurrentDataPredictor(
        start=datetime.now(), dal=dal, max_date=max_date  # type: ignore
    )
    await predictor.update_params()
    for item in predictor._data[:10]:
        print(item)
    result = await predictor.get_next_timestamp(
        start=datetime.now(), target_entities=800
    )
    print(result)


if __name__ == "__main__":
    load_dotenv()
    sys.path.append(os.getcwd())
    asyncio.run(main())
