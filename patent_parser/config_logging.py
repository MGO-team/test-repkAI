import logging
import logging.config

from datetime import datetime
from pathlib import Path
from config import LOG_DIR


now = datetime.now()
formatted_datetime = now.strftime("%Y%m%d%H%M")


if not LOG_DIR or LOG_DIR is None:
    LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR = Path(LOG_DIR)
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s"},
        "simple": {"format": "[%(asctime)s]-[%(name)s]-[%(levelname)s]: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / f"{formatted_datetime}_parser.log",
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
