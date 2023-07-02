import pytest

from band_tracker.core.artist import Artist


class TestArtist:
    def test_upcoming_events_positive(self) -> None:
        artist = Artist(
            id="",
            name="",
            shortname="",
            spotify_link="",
            link="",
            upcoming_events_amount=2,
            score=0.5,
            genres=[],
            _source_specific_data={},
        )
        assert artist.has_upcoming_events


if __name__ == "__main__":
    pytest.main()
