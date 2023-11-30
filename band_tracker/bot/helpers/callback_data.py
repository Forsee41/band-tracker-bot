from telegram import CallbackQuery
from telegram.ext import InvalidCallbackData


def get_callback_data(query: CallbackQuery | None) -> str:
    if query is None:
        raise InvalidCallbackData("Can't find callback query")
    if query.data is None:
        raise InvalidCallbackData("Can't find callback query data")
    data_parts = query.data.split()
    if len(data_parts) != 2:
        raise InvalidCallbackData(f"Invalid callback data, {query.data}")
    result = data_parts[1]
    return result


def get_multiple_fields(query: CallbackQuery | None) -> list[str]:
    if query is None:
        raise InvalidCallbackData("Can't find callback query")
    if query.data is None:
        raise InvalidCallbackData("Can't find callback query data")
    result = query.data.split()
    if len(result) < 2:
        raise InvalidCallbackData(f"Not enough fields in callback data, {query.data}")
    return result
