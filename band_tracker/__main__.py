from band_tracker.config.log import load_log_config
from band_tracker.config.env_loader import load_dotenv, load_env_vars
import logging


def main() -> None:
    load_log_config()
    log = logging.getLogger(__name__)

    load_dotenv()
    try:
        env_vars = load_env_vars()
    except EnvironmentError as e:
        log.critical(e)
        return
    assert env_vars


if __name__ == "__main__":
    main()
