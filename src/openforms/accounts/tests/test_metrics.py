from django.test import TestCase

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_users
from .factories import UserFactory


class UserCountMetricTests(MetricsAssertMixin, TestCase):
    def test_count_users_by_type(self):
        UserFactory.create_batch(3)
        UserFactory.create_batch(2, is_staff=True)
        UserFactory.create_batch(4, is_staff=True, is_superuser=True)

        result = count_users(CallbackOptions())

        counts_by_type = {
            observation.attributes["type"]: observation.value for observation in result
        }
        self.assertEqual(
            counts_by_type,
            {
                "all": 3 + 2 + 4,
                "staff": 2 + 4,
                "superuser": 4,
            },
        )
        self.assertMarkedGlobal(result)
