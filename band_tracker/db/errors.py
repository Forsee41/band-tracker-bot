class DALError(Exception):
    """Raised when trying to perfrom invalid operation in DAL"""


class UserAlreadyExists(Exception):
    """Raised when trying to add a user with tg id, that is already present in db"""


class ArtistNotFound(Exception):
    """Raised when artist is not present in database"""


class UserNotFound(Exception):
    """Raised when user is not present in database"""
