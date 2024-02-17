import logging

from band_tracker.config.env_loader import get_log_level


def load_log_config() -> None:
    log_lvl = get_log_level()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=log_lvl
    )
    logging.getLogger(__name__).info(
        f"Basic log config initialized, log level: {log_lvl}"
    )
