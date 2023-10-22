from datetime import datetime, timedelta
from typing import Callable

import pytest

from band_tracker.updater.timestamp_predictor import CurrentDataPredictor


class PredictorDALMock:
    def set_data(self, data: list[tuple[datetime, int]]) -> None:
        self.data = data

    async def get_event_amounts(self) -> list[tuple[datetime, int]]:
        return self.data


class TestCurrentDataPredictor:
    @staticmethod
    @pytest.fixture(scope="class")
    def predictor() -> CurrentDataPredictor:
        dal = PredictorDALMock()
        start_datetime = datetime(year=2020, month=1, day=1)
        result = CurrentDataPredictor(dal=dal, start=start_datetime)
        return result

    @staticmethod
    @pytest.fixture(scope="class")
    def make_predictor_data() -> Callable[[list[int]], list[tuple[datetime, int]]]:
        def data_maker(input: list[int]) -> list[tuple[datetime, int]]:
            result = []
            date = datetime(year=2020, month=1, day=1)
            for value in input:
                result.append((date, value))
                date += timedelta(days=1)
            return result

        return data_maker


if __name__ == "__main__":
    pytest.main()
