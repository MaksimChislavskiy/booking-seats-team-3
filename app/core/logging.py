import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from rich.logging import RichHandler


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"


def setup_logging() -> logging.Logger:
    """Настраивает централизованное логирование строго по ТЗ."""
    log_format = "%(asctime)s [%(levelname)s] [%(user)s] %(message)s"

    console_handler = RichHandler(rich_tracebacks=True, show_path=False)
    console_handler.setFormatter(logging.Formatter(log_format))

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,      # 10 МБ
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger("cafe_booking")
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    def user_filter(record: logging.LogRecord) -> bool:
        record.user = getattr(record, "user", "SYSTEM")
        return True

    logger.addFilter(user_filter)

    return logger
