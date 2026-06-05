import logging
from enum import Enum


class LogLevel(Enum):
    """
    Enum of supported logging levels.
    """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


RESET = "\033[0m"
DARK_GRAY = "\033[90m"

LEVEL_COLORS = {
    LogLevel.DEBUG: "\033[35m",
    LogLevel.INFO: "\033[34m",
    LogLevel.WARNING: "\033[33m",
    LogLevel.ERROR: "\033[31m",
    LogLevel.CRITICAL: "\033[41m",
}


class ColoredFormatter(logging.Formatter):
    """
    A logging formatter that adds ANSI colors to log output.
    """
    format_str = "%(asctime)s %(levelname)s %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with colored output.

        :param record: The log record to format.
        :return: The formatted log message.
        """
        formatter = logging.Formatter(
            self.format_str,
            "%Y-%m-%d %H:%M:%S",
        )

        level = LogLevel(record.levelno)
        level_color = LEVEL_COLORS.get(level, RESET)

        original_levelname = record.levelname

        padded_levelname = f"{original_levelname:<8}"
        record.levelname = f"{level_color}{padded_levelname}{RESET}"

        message = formatter.format(record)

        if hasattr(record, "asctime"):
            message = message.replace(
                record.asctime,
                f"{DARK_GRAY}{record.asctime}{RESET}",
                1,
            )

        record.levelname = original_levelname

        return message


def get_logger(
    name: str = "Main Logger",
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Create or retrieve a configured logger.

    :param name: The logger name.
    :param level: The logger level.
    :return: The configured logger.
    """  
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(ColoredFormatter())

        logger.addHandler(handler)

    return logger


logger: logging.Logger = get_logger()