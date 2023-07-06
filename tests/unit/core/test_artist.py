import pytest

from band_tracker.core.artist import Artist


class TestArtist:
    def test_upcoming_events_positive(self) -> None:
        artist = Artist(
            id="",
            name="",
            spotify_link=None,
            tickets_link=None,
            inst_link=None,
            youtube_link=None,
            upcoming_events_amount=2,
            _source_specific_data=None,
        )
        assert artist.has_upcoming_events


if __name__ == "__main__":
    pytest.main()
