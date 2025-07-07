import smtplib
import socket
from unittest import mock
from unittest.mock import patch
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core import mail
from django.template.defaultfilters import yesno
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from django_yubin import settings as yubin_settings
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.emails.connection_check import LabelValue, check_email_backend
from openforms.utils.tests.webtest_base import WebTestPyQueryMixin


def replace(mapping, **kwargs):
    assert kwargs
    d = mapping.copy()
    d.update(kwargs)
    return d


smtp_settings = dict(
    EMAIL_HOST="localhost",
    EMAIL_PORT=252525,
    EMAIL_HOST_USER="foo",
    EMAIL_HOST_PASSWORD="bar",
    EMAIL_USE_TLS=False,
    EMAIL_USE_SSL=False,
    EMAIL_TIMEOUT=10,
    EMAIL_SSL_KEYFILE=None,
    EMAIL_SSL_CERTFILE=None,
    # NOTE we use the smtp backend for this test because we can make it fail with mock/patch
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    DEFAULT_FROM_EMAIL="sender@bar.bazz",
)


class CheckEmailSettingsFunctionTests(TestCase):
    maxDiff = None

    def test_ok(self):
        res = check_email_backend("receiver@bar.bazz")

        self.assertEqual(res.success, True)
        self.assertEqual(
            res.feedback,
            [
                _(
                    "Successfully sent test message to %(recipients)s, please check the mailbox."
                )
                % {"recipients": "receiver@bar.bazz"}
            ],
        )

        email_message = mail.outbox[0]
        self.assertEqual(
            email_message.subject, _("Open Forms email configuration test")
        )

    @override_settings(
        **replace(
            smtp_settings,
            EMAIL_BACKEND="django_yubin.backends.QueuedEmailBackend",
        )
    )
    def test_init_yubin(self):
        with patch.multiple(
            yubin_settings,
            PAUSE_SEND=True,
            MAILER_TEST_MODE=True,
            USE_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        ):
            res = check_email_backend("receiver@bar.bazz")

        self.assertEqual(res.success, True)
        self.assertEqual(
            res.feedback,
            [
                _("Django-yubin detected:"),
                LabelValue(
                    label="MAILER_USE_BACKEND",
                    value="django.core.mail.backends.smtp.EmailBackend",
                ),
                LabelValue(label="MAILER_PAUSE_SEND", value=True),
                LabelValue(label="MAILER_TEST_MODE", value=True),
                LabelValue(label="MAILER_TEST_EMAIL", value=""),
                _(
                    "Successfully sent test message to %(recipients)s, please check the mailbox."
                )
                % {"recipients": "receiver@bar.bazz"},
                _(
                    "If the message doesn't arrive check the Django-yubin queue and cronjob."
                ),
            ],
        )
        self.assertIsNone(res.exception)

    @override_settings(**replace(smtp_settings, EMAIL_HOST=""))
    def test_init_bad_host_exception(self):
        res = check_email_backend("receiver@bar.bazz")

        self.assertEqual(res.success, False)
        self.assertEqual(
            res.feedback,
            [
                _("Exception while trying to send test message to %(recipients)s")
                % {"recipients": res.recipients_str}
            ],
        )
        self.assertIsInstance(res.exception, smtplib.SMTPServerDisconnected)

    @override_settings(**replace(smtp_settings, EMAIL_USE_TLS=True, EMAIL_USE_SSL=True))
    def test_init_bad_tls_ssl_exception(self):
        res = check_email_backend("receiver@bar.bazz")

        self.assertEqual(res.success, False)
        self.assertEqual(
            res.feedback,
            [
                _("Exception while trying to send test message to %(recipients)s")
                % {"recipients": res.recipients_str}
            ],
        )
        self.assertIsInstance(res.exception, ValueError)

    @override_settings(**smtp_settings)
    def test_login_smtp_exception(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = smtplib.SMTPException()
            res = check_email_backend("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [
                    _("Exception while trying to send test message to %(recipients)s")
                    % {"recipients": res.recipients_str}
                ],
            )
            self.assertIsInstance(res.exception, smtplib.SMTPException)

    @override_settings(**smtp_settings)
    def test_login_socket_error(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = OSError()
            res = check_email_backend("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [
                    _("Exception while trying to send test message to %(recipients)s")
                    % {"recipients": res.recipients_str}
                ],
            )
            self.assertIsInstance(res.exception, socket.error)


@disable_admin_mfa()
class CheckEmailSettingsAdminViewTest(WebTestPyQueryMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.permission = Permission.objects.get(codename="email_backend_test")

    def test_requires_auth(self):
        url = reverse("admin_email_test")
        redirect_url = f"{settings.LOGIN_URL}?next={quote(url)}"

        with self.subTest("anon"):
            response = self.app.get(url, status=302)  # to login
            self.assertRedirects(response, redirect_url, target_status_code=302)

        with self.subTest("user"):
            user = UserFactory()
            self.app.set_user(user)
            response = self.app.get(url, status=302)  # to login
            self.assertRedirects(response, redirect_url, target_status_code=302)

        with self.subTest("staff"):
            user = StaffUserFactory()
            self.app.set_user(user)
            response = self.app.get(url, status=403)  # no perms

        with self.subTest("staff with permission"):
            user = StaffUserFactory()
            user.user_permissions.add(self.permission)
            self.app.set_user(user)
            response = self.app.get(url, status=200)

    def test_run_check_pass(self):
        url = reverse("admin_email_test")
        user = StaffUserFactory()
        user.user_permissions.add(self.permission)
        self.app.set_user(user)
        response = self.app.get(url, status=200)

        self.assertPyQueryExists(response, f"form[action='{url}']")
        self.assertPyQueryExists(response, "input[name='recipient']")

        # send the form
        form = [f for f in response.forms.values() if f.action == url][0]
        form["recipient"] = "receiver@bar.bazz"
        response = form.submit()
        self.assertEqual(response.status_code, 200)

        email_message = mail.outbox[0]
        self.assertEqual(
            email_message.subject, _("Open Forms email configuration test")
        )

        # grab translations, use the yesno template filter because its weird
        yes = yesno(True)
        success = _("Success")

        self.assertPyQueryExists(response, f"form[action='{url}']")
        self.assertPyQueryExists(response, "table[class='result-table']")
        self.assertPyQueryExists(
            response,
            f"table[class='result-table'] tr td:contains('{success}') + td:contains('{yes}')",
        )

    @override_settings(**smtp_settings)
    def test_run_check_fail(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = smtplib.SMTPException(
                "Foo Exception"
            )

            url = reverse("admin_email_test")
            user = StaffUserFactory()
            user.user_permissions.add(self.permission)
            self.app.set_user(user)
            response = self.app.get(url, status=200)

            self.assertPyQueryExists(response, f"form[action='{url}']")
            self.assertPyQueryExists(response, "input[name='recipient']")

            # send the form
            form = [f for f in response.forms.values() if f.action == url][0]
            form["recipient"] = "receiver@bar.bazz"
            response = form.submit()
            self.assertEqual(response.status_code, 200)
            mock_smtp.assert_called()
            mock_smtp.return_value.login.assert_called()

            # grab translations, use the yesno template filter because its weird
            no = yesno(False)
            success = _("Success")

            self.assertPyQueryExists(response, f"form[action='{url}']")
            self.assertPyQueryExists(response, "table[class='result-table']")
            self.assertPyQueryExists(
                response,
                f"table[class='result-table'] tr td:contains('{success}') + td:contains('{no}')",
            )
            self.assertPyQueryExists(
                response,
                "table[class='result-table'] tr td code:contains('Foo Exception')",
            )
