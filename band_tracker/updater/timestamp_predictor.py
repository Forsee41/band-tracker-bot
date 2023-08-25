import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta


class TimestampPredictor(ABC):
    @abstractmethod
    def get_next_timestamp(
        self, current_timestamp: datetime, target_entities: int
    ) -> datetime:
        """Returns best fitting timestamp"""


class LinearPredictor(TimestampPredictor):
    """Using ax+b formula for predictions. The unit is day"""

    def __init__(self, a: float, b: float) -> None:
        self._a = a
        self._b = b
        self._start = datetime.now()

    def get_next_timestamp(
        self, starting_timestamp: datetime, target_entities: int
    ) -> datetime:
        time_passed_to_start: timedelta = starting_timestamp - self._start
        days_passed_to_start: int = time_passed_to_start.days
        left_integr = (
            (days_passed_to_start**2) * self._a * 0.5
        ) + days_passed_to_start * self._b
        a_term = self._a * 0.5
        b_term = self._b
        c_term = -(left_integr + target_entities)
        disc = b_term**2 - (4 * a_term * c_term)
        solution1 = (-b_term - math.sqrt(disc)) / (2 * a_term)
        solution2 = (-b_term + math.sqrt(disc)) / (2 * a_term)
        real_solution = max([solution1, solution2])
        return self._start + timedelta(days=real_solution)
