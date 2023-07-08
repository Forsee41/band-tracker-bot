from band_tracker.core.enums import EventSource


class DeserializationError(Exception):
    def __init__(self, error_str: str, api: EventSource) -> None:
        self.api = api
        super().__init__(error_str)
