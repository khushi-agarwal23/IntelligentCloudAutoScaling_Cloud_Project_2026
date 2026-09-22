import logging
import sys
from ..config import settings


def setup_logger(name: str = "backend") -> logging.Logger:
    """Configures structured logging for cloud deployment and local debugging."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)
    return logger


logger = setup_logger()
