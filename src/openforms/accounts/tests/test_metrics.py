from unittest.mock import MagicMock, patch

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase, override_settings

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_users, login_failures, logins, logouts, user_lockouts
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


class LoginLogoutMetricTests(TestCase):
    @patch.object(logins, "add", wraps=logins.add)
    def test_user_logins_incremented(self, mock_add: MagicMock):
        user = UserFactory.create(username="admin", password="secret")
        request = RequestFactory().post("/admin/login/")
        request.session = SessionStore("dummy")
        authenticate(request=request, username="admin", password="secret")
        login(
            request, user, backend="openforms.accounts.backends.UserModelEmailBackend"
        )

        mock_add.assert_called_once_with(
            1,
            attributes={
                "http_target": "/admin/login/",
                "username": "admin",
            },
        )

    @patch.object(logouts, "add", wraps=logouts.add)
    def test_user_logouts_incremented(self, mock_add: MagicMock):
        user = UserFactory.create(username="admin", password="secret")
        request = RequestFactory().post("/admin/logout/")
        request.session = SessionStore("dummy")
        request.user = user

        logout(request)

        mock_add.assert_called_once_with(
            1,
            attributes={
                "username": "admin",
            },
        )

    @patch.object(logouts, "add", wraps=logouts.add)
    def test_user_logouts_incremented_even_for_anon_user(self, mock_add: MagicMock):
        request = RequestFactory().post("/admin/logout/")
        request.session = SessionStore("dummy")
        request.user = AnonymousUser()

        logout(request)

        mock_add.assert_not_called()
