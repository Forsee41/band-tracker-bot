from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import sympy


class TimestampPredictor(ABC):
    @abstractmethod
    def get_next_timestamp(self, start: datetime, target_entities: int) -> datetime:
        """Returns best fitting timestamp"""

    @property
    def start(self) -> datetime:
        ...


class LinearPredictor(TimestampPredictor):
    """Using ax+b formula for predictions. The unit is day"""

    def __init__(self, a: float, b: float, start: datetime | None) -> None:
        self._a = a
        self._b = b
        self._start = start if start is not None else datetime.now()

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

    @property
    def start(self) -> datetime:
        return self._start

    def get_next_timestamp(self, start: datetime, target_entities: int) -> datetime:
        time_passed_to_start: timedelta = start - self._start
        days_passed_to_start: int = time_passed_to_start.days
        target_days_passed = self._calculate(
            start=days_passed_to_start, target_area=target_entities
        )
        return self._start + timedelta(days=int(target_days_passed))
