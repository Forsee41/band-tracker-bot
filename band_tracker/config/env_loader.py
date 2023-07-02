import dotenv
from typing import NamedTuple
import os


class EnvVars(NamedTuple):
    TG_BOT_TOKEN: str
    EVENTS_API_LOGIN: str
    EVENTS_API_SECRET: str


def load_dotenv() -> None:
    dotenv.load_dotenv()


def load_env_vars() -> EnvVars:
    env_var_dict = {"TG_BOT_TOKEN": "", "EVENTS_API_LOGIN": "", "EVENTS_API_SECRET": ""}

    for key in env_var_dict:
        try:
            env_value = os.environ[key]
            env_var_dict[key] = env_value

        except KeyError:
            raise EnvironmentError(f"{key} env var is not found")

    return EnvVars(**env_var_dict)
