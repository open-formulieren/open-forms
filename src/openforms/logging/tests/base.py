from openforms.logging.models import TimelineLogProxy


class LoggingTestMixin:
    def assertLogExtraDataEquals(self, log: TimelineLogProxy, **extra_data):
        self.assertIsNotNone(log.extra_data)
        self.assertNotEqual(extra_data, dict())

        for key, value in extra_data.items():
            self.assertIn(key, log.extra_data)
            self.assertEqual(log.extra_data[key], value)

    def assertLogEventLast(self, event_name: str, **extra_data):
        log = TimelineLogProxy.objects.last()
        self.assertIsNotNone(log)
        self.assertLogExtraDataEquals(log, log_event=event_name)
        if extra_data:
            self.assertLogExtraDataEquals(log, **extra_data)
