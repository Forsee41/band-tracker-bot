from band_tracker.core.enums import EventSource


class WrongChunkException(Exception):
    """Chunk with no idle pages was given"""


class InvalidResponseStructureError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class DescriptionFetchError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(Exception):
    """Invalid API token was given"""


class UnexpectedFaultResponseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class AllTokensViolation(Exception):
    """All tokens have been violated"""


class QuotaViolation(Exception):
    """Day quota limit exceeded"""

    # errorcode: policies.ratelimit.QuotaViolation


class RateLimitViolation(Exception):
    """Rate limit exceeded"""


class EmptyResponseException(Exception):
    def __init__(self, error_str: str, api: EventSource) -> None:
        self.api = api
        super().__init__(error_str)


class UpdateError(Exception):
    def __init__(
        self, *args, exceptions: list[Exception], **kwargs  # noqa: ignore
    ) -> None:
        super().__init__(*args, **kwargs)
        self.exceptions = exceptions


class PredictorError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
