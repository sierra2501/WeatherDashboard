import logging.config
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # weather/package/
LOG_DIR = os.path.join(BASE_DIR, "..", "log")            # weather/log/
LOG_FILE = os.path.join(LOG_DIR, "weather.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s;%(name)s;%(levelname)s;%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": LOG_FILE,  # 絶対パスに変更
            "level": "INFO",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)  # logフォルダがなければ作成
    logging.config.dictConfig(LOGGING_CONFIG)