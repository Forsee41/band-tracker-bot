import os
from typing import NamedTuple


class TgBotEnvVars(NamedTuple):
    TG_BOT_TOKEN: str


class EventsApiEnvVars(NamedTuple):
    CONCERTS_API_TOKEN: str
    CONCERTS_API_SECRET: str
    CONCERTS_API_URL: str


class DBEnvVars(NamedTuple):
    DB_LOGIN: str
    DB_PASSWORD: str
    DB_IP: str
    DB_PORT: str
    DB_NAME: str


class MQEnvVars(NamedTuple):
    MQ_URI: str
    MQ_EXCHANGE: str


def _load_vars(names: list[str]) -> dict[str, str]:
    result = {}
    for var_name in names:
        try:
            env_value = os.environ[var_name]
        except KeyError:
            raise EnvironmentError(f"{var_name} env var is not found")
        result[var_name] = env_value
    return result


def mq_env_vars() -> MQEnvVars:
    env_var_names = [
        "MQ_URI",
        "MQ_EXCHANGE",
    ]
    env_var_dict = _load_vars(env_var_names)

    return MQEnvVars(**env_var_dict)


def tg_bot_env_vars() -> TgBotEnvVars:
    env_var_names = ["TG_BOT_TOKEN"]
    env_var_dict = _load_vars(env_var_names)

    return TgBotEnvVars(**env_var_dict)


def events_api_env_vars() -> EventsApiEnvVars:
    env_var_names = ["CONCERTS_API_TOKEN", "CONCERTS_API_SECRET", "CONCERTS_API_URL"]
    env_var_dict = _load_vars(env_var_names)

    return EventsApiEnvVars(**env_var_dict)


def db_env_vars() -> DBEnvVars:
    env_var_names = [
        "DB_LOGIN",
        "DB_PASSWORD",
        "DB_IP",
        "DB_PORT",
        "DB_NAME",
    ]
    env_var_dict = _load_vars(env_var_names)

    return DBEnvVars(**env_var_dict)
