from copy import copy
from datetime import datetime, timedelta
from typing import Callable

import pytest

from band_tracker.updater.timestamp_predictor import CurrentDataPredictor


class PredictorDALMock:
    def __init__(self) -> None:
        self.data: list[tuple[datetime, int]] = []

    def set_data(self, data: list[tuple[datetime, int]]) -> None:
        self.data = data

    async def get_event_amounts(self) -> list[tuple[datetime, int]]:
        return self.data


predictor_start = datetime(year=2020, month=1, day=1)

PredictorData = list[tuple[datetime, int]]
PredictorDataFixture = Callable[[list[int]], PredictorData]
PredictorFixture = Callable[[PredictorData], CurrentDataPredictor]


class TestCurrentDataPredictor:
    @staticmethod
    @pytest.fixture(scope="class")
    def predictor() -> PredictorFixture:
        def create_predictor(data: PredictorData) -> CurrentDataPredictor:
            dal = PredictorDALMock()
            dal.set_data(data)
            start_datetime = predictor_start
            result = CurrentDataPredictor(dal=dal, start=start_datetime)
            return result

        return create_predictor

    @staticmethod
    @pytest.fixture(scope="class")
    def predictor_data() -> PredictorDataFixture:
        def data_maker(input: list[int]) -> list[tuple[datetime, int]]:
            result = []
            date = copy(predictor_start)
            for value in input:
                if value > 0:
                    result.append((date, value))
                date += timedelta(days=1)
            return result

        return data_maker

    @pytest.mark.parametrize(
        ("data", "target", "expected_result"),
        (
            ([5, 5, 5, 5], 15, 2),
            ([5, 5, 5, 5], 16, 3),
            ([5, 5, 5, 5], 5, 0),
            ([5, 5, 5, 5], 6, 1),
            ([5, 5, 5, 5], 1, 0),
            ([5, 0, 0, 5], 4, 0),
            ([5, 0, 0, 5], 6, 3),
            ([5, 0, 0, 5], 11, 731),
            ([5, 0, 0, 0], 10, 731),
            ([0, 0, 0, 0], 10, 731),
        ),
    )
    async def test_predict_from_start(
        self,
        predictor: PredictorFixture,
        predictor_data: PredictorDataFixture,
        data: list[int],
        target: int,
        expected_result: int,
    ) -> None:
        if expected_result > 0:
            expected_result -= 1
        prepared_data = predictor_data(data)
        pd = predictor(prepared_data)
        await pd.update_params()
        result_date = await pd.get_next_timestamp(
            start=predictor_start, target_entities=target
        )
        assert result_date == predictor_start + timedelta(days=expected_result)

    async def test_empty_data(
        self,
        predictor: PredictorFixture,
        predictor_data: PredictorDataFixture,
    ) -> None:
        prepared_data = predictor_data([])
        pd = predictor(prepared_data)
        await pd.update_params()
        result_date = await pd.get_next_timestamp(
            start=predictor_start, target_entities=1
        )
        assert result_date == predictor_start + timedelta(days=730)

    @pytest.mark.parametrize(
        ("data", "start", "target", "expected_result"),
        (
            ([5, 5, 5, 5], 1, 15, 3),
            ([5, 5, 5, 5], 1, 11, 3),
            ([5, 5, 5, 5], 4, 15, 731),
            ([5, 5, 5, 5], 4, 1, 731),
        ),
    )
    async def test_predict_from_middle(
        self,
        predictor: PredictorFixture,
        predictor_data: PredictorDataFixture,
        data: list[int],
        target: int,
        expected_result: int,
        start: int,
    ) -> None:
        if expected_result > 0:
            expected_result -= 1
        prepared_data = predictor_data(data)
        pd = predictor(prepared_data)
        await pd.update_params()
        start_date = predictor_start + timedelta(days=start)
        result_date = await pd.get_next_timestamp(
            start=start_date, target_entities=target
        )
        assert result_date == predictor_start + timedelta(days=expected_result)


if __name__ == "__main__":
    pytest.main()
