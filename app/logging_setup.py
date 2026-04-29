import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config import settings


def setup_logging() -> None:
    """Configure app logging with daily rotation and 30-day retention."""
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / settings.log_file_name

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers when reloader imports app multiple times.
    for handler in list(root_logger.handlers):
        if isinstance(handler, TimedRotatingFileHandler):
            if Path(getattr(handler, "baseFilename", "")) == log_file:
                return

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
