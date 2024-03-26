import logging
from contextlib import contextmanager
from typing import Iterator

from django.test.utils import TestContextDecorator


class disable_logging(TestContextDecorator):
    def enable(self):
        logging.disable(logging.CRITICAL)

    def disable(self):
        logging.disable(logging.NOTSET)


@contextmanager
def ensure_logger_level(level: str = "INFO", name="openforms") -> Iterator[None]:
    """
    Set the (minimum) level for a given logger.

    Base or individual settings may tweak the log level to reduce the overload for the
    developer, but this affects tests that verify that log records are "written" by
    application code for a certain log level.

    This context manager allows you to pin the log level for a given text, irrespective
    of individual preferences/developer settings.
    """
    logger = logging.getLogger(name)
    original_level = logger.getEffectiveLevel()

    logger.setLevel(logging._nameToLevel[level])
    yield
    logger.setLevel(original_level)
