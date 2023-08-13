class InvalidResponseStructureError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(Exception):
    """Invalid API token was given"""


class UnexpectedFaultResponseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class RateLimitQuotaViolation(Exception):
    """Quota limit exceeded"""

    def __init__(self, page_number: int) -> None:
        self.page_number = page_number
