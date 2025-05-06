import logging  # noqa: TID251 -- structlog uses the same level constants

from django.test.utils import TestContextDecorator


class disable_logging(TestContextDecorator):
    def enable(self):
        logging.disable(logging.CRITICAL)

    def disable(self):
        logging.disable(logging.NOTSET)
