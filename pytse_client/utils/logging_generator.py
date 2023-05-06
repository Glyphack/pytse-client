import logging
from pytse_client.config import LOGGER_NAME


def get_logger(name: str, level: int):
    logger = logging.getLogger(f"{LOGGER_NAME}_{name}")
    logger.setLevel(level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
