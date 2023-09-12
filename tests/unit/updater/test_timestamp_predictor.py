from datetime import datetime

import pytest

from band_tracker.updater.timestamp_predictor import LinearPredictor


class TestLinearPredictor:
    @pytest.mark.skip
    @pytest.mark.parametrize(
        ("start", "target_units", "expected_end"),
        (
            [
                datetime(year=2000, month=1, day=1),
                27,
                datetime(year=2000, month=1, day=3),
            ],
            [
                datetime(year=2000, month=1, day=1),
                49,
                datetime(year=2000, month=1, day=7),
            ],
        ),
    )
    def test_int_a(
        self, start: datetime, target_units: int, expected_end: datetime
    ) -> None:
        predictor = LinearPredictor(
            a=-1,
            b=10,
            start=datetime(year=2000, month=1, day=1),
        )
        result = predictor.get_next_timestamp(
            starting_timestamp=start, target_entities=target_units
        )
        assert result == expected_end

    @pytest.mark.skip
    @pytest.mark.parametrize(
        ("start", "target_units", "expected_end"),
        (
            [
                datetime(year=2000, month=1, day=1),
                270,
                datetime(year=2000, month=1, day=30),
            ],
            [
                datetime(year=2000, month=1, day=1),
                490,
                datetime(year=2000, month=3, day=10),
            ],
        ),
    )
    def test_float_a(
        self, start: datetime, target_units: int, expected_end: datetime
    ) -> None:
        predictor = LinearPredictor(
            a=-0.1,
            b=10,
            start=datetime(year=2000, month=1, day=1),
        )
        result = predictor.get_next_timestamp(
            starting_timestamp=start, target_entities=target_units
        )
        assert result == expected_end

    def test_numeric(self) -> None:
        predictor = LinearPredictor(
            a=-1,
            b=10,
            start=datetime(year=2000, month=1, day=1),
        )
        result = predictor._calculate(start=0, target_area=18)
        assert result == 2


if __name__ == "__main__":
    pytest.main()
