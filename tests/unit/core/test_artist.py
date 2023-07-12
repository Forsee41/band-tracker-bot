from uuid import uuid4

import pytest

from band_tracker.core.artist import Artist, ArtistSocials


class TestArtist:
    def test_artist_constructor(self) -> None:
        socials = ArtistSocials(instagram=None, spotify=None, youtube=None)
        artist = Artist(
            id=uuid4(), name="", tickets_link=None, socials=socials, image=None
        )
        assert artist


if __name__ == "__main__":
    pytest.main()
