import logging  # noqa: TID251
from contextlib import contextmanager

import structlog

logger = structlog.stdlib.get_logger(__name__)


@contextmanager
def supress_errors():
    try:
        yield
    except Exception as exc:
        logger.error("log_saving_failed", exc_info=exc)


class TimelineLoggerHandler(logging.Handler):
    """
    Save a log record into a django-timeline-logger record.

    Logs saved to the local database are typically intended to be easily accessible,
    e.g. audit logs, without requiring access to a dedicated log storage like Loki.

    This handler goes hand-in-hand with structlog:

    * it looks at the structlog event to call additional (pre)-processing, allowing
      additional metadata extraction
    * the additional log attributes are stored as structured data
    """

    @supress_errors()
    def emit(self, record: logging.LogRecord):
        print(record)
