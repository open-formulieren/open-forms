from unittest.mock import MagicMock, patch

from django.contrib.auth import authenticate
from django.test import RequestFactory, TestCase, override_settings

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_users, login_failures, user_lockouts
from .factories import UserFactory


class UserCountMetricTests(MetricsAssertMixin, TestCase):
    def test_count_users_by_type(self):
        UserFactory.create_batch(3)
        UserFactory.create_batch(2, is_staff=True)
        UserFactory.create_batch(4, is_staff=True, is_superuser=True)

        result = count_users(CallbackOptions())

        counts_by_type = {
            observation.attributes["type"]: observation.value
            for observation in result
            if observation.attributes
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


class LoginFailuresMetricTests(TestCase):
    @patch.object(login_failures, "add", wraps=login_failures.add)
    def test_login_failures_tracked(self, mock_add: MagicMock):
        request = RequestFactory().post("/admin/login/")

        # invalid credentials, no such user exists
        authenticate(request=request, username="foo", password="bar")

        mock_add.assert_called()


@override_settings(AXES_FAILURE_LIMIT=2)
class LockoutsMetricTests(TestCase):
    @patch.object(user_lockouts, "add", wraps=user_lockouts.add)
    def test_no_counter_increment_if_not_yet_locked_out(self, mock_add: MagicMock):
        request = RequestFactory().post("/admin/login/")

        with self.subTest(attempt=1, lockout=False):
            # invalid credentials, no such user exists
            authenticate(request=request, username="foo", password="bar")

            self.assertFalse(mock_add.called)

        with self.subTest(attempt=2, lockout=True):
            # invalid credentials, no such user exists
            authenticate(request=request, username="foo", password="still wrong")

            self.assertTrue(mock_add.called)
