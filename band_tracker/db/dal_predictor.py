import logging
from datetime import datetime

from sqlalchemy import text

from band_tracker.db.session import AsyncSessionmaker

log = logging.getLogger(__name__)


class PredictorDAL:
    def __init__(self, sessionmaker: AsyncSessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def get_event_amounts(self) -> list[tuple[datetime, int]]:
        # Using raw sql for query optimization, query has no params
        stmt = text(
            """
        SELECT DATE_TRUNC('day', start_date) as dates, count(id)
        FROM event
        GROUP BY DATE_TRUNC('day', start_date)
        ORDER BY DATE_TRUNC('day', start_date)
        """
        )
        async with self.sessionmaker.session() as session:
            raw_result = await session.execute(stmt)
            data = raw_result.fetchall()
        result = data
        return result
