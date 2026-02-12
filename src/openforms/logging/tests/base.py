from typing import TYPE_CHECKING
from unittest import TestCase

from openforms.logging.models import TimelineLogProxy

if TYPE_CHECKING:
    Base = TestCase
else:
    Base = object


class LoggingTestMixin(Base):
    def assertLogExtraDataEquals(self, log: TimelineLogProxy, **extra_data):
        self.assertIsNotNone(log.extra_data)
        self.assertNotEqual(extra_data, dict())

        for key, value in extra_data.items():
            self.assertIn(key, log.extra_data)
            self.assertEqual(log.extra_data[key], value)

    def assertLogEventLast(self, event_name: str, **extra_data):
        log = TimelineLogProxy.objects.last()
        assert log is not None
        self.assertLogExtraDataEquals(log, log_event=event_name)
        if extra_data:
            self.assertLogExtraDataEquals(log, **extra_data)
