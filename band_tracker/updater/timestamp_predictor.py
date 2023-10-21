from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import sympy

from band_tracker.db.dal import PredictorDAL


class TimestampPredictor(ABC):
    @abstractmethod
    async def get_next_timestamp(
        self, start: datetime, target_entities: int
    ) -> datetime:
        """Returns best fitting timestamp"""

    @abstractmethod
    def start(self) -> datetime:
        """get value of the start property"""

    @abstractmethod
    async def update_params(self) -> None:
        """Updates parameters for predictor"""


class LinearPredictor(TimestampPredictor):
    """Using ax+b formula for predictions. The unit is day"""

    def __init__(self, a: float, b: float, start: datetime | None) -> None:
        self._a = a
        self._b = b
        self._start = start if start is not None else datetime.now()

    async def update_params(self) -> None:
        assert self._a
        assert self._b
        assert self._start
        """Updates parameters for predictor"""

    def _calculate(self, start: int, target_area: int) -> int:
        a = self._a
        b = self._b
        c = target_area
        x1 = start
        x2 = sympy.symbols("x2")
        eq = sympy.Eq(((a * (x1 + x2) + (2 * b)) / 2) * (x2 - x1), (c))
        solution_raw = sympy.solve(eq, x2)
        solution = []
        for item in solution_raw:
            if item.is_real:
                solution.append(int(item))
        return min(solution)

    def start(self) -> datetime:
        return self._start

    async def get_next_timestamp(
        self, start: datetime, target_entities: int
    ) -> datetime:
        time_passed_to_start: timedelta = start - self._start
        days_passed_to_start: int = time_passed_to_start.days
        target_days_passed = self._calculate(
            start=days_passed_to_start, target_area=target_entities
        )
        return self._start + timedelta(days=int(target_days_passed))


class CurrentDataPredictor(TimestampPredictor):
    def __init__(self, dal: PredictorDAL, start: datetime = datetime.now()) -> None:
        self._start = start
        self._dal = dal
        self._data: list[tuple[datetime, int]] = []

    async def update_params(self) -> None:
        data = await self._dal.get_event_amounts()
        self._data = list(filter(lambda x: x[0] >= self._start, data))

    def start(self) -> datetime:
        return self._start

    async def get_next_timestamp(
        self, start: datetime, target_entities: int
    ) -> datetime:
        max_date = self._start + timedelta(days=730)
        if start == max_date:
            return max_date + timedelta(days=1)

        data_iter = iter(self._data)
        try:
            while (start_item := next(data_iter))[0] <= start - timedelta(days=1):
                continue
            entities_cnt = start_item[1]
            for item in data_iter:
                entities_cnt += item[1]
                if entities_cnt >= target_entities:
                    # data might miss days, no reason to pick the last non-empty day
                    return item[0] - timedelta(days=1)
        except StopIteration:
            pass

        return max_date
