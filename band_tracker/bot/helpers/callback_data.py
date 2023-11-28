from telegram import CallbackQuery
from telegram.ext import InvalidCallbackData


def get_callback_data(query: CallbackQuery | None) -> str:
    if query is None:
        raise InvalidCallbackData(
            "Subscribe button callback handler can't find callback query"
        )
    if query.data is None:
        raise InvalidCallbackData(
            "Subscribe button callback handler can't find callback query data"
        )
    data_parts = query.data.split()
    if len(data_parts) != 2:
        raise InvalidCallbackData(
            "Subscribe button callback handler got invalid callback data,"
            f" {query.data}"
        )
    result = data_parts[1]
    return result
