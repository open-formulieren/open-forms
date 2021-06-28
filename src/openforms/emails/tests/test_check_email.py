import smtplib
import socket
from unittest import mock
from urllib.parse import quote

from django.conf import settings
from django.template.defaultfilters import yesno
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.emails.connection_check import check_smtp_settings
from openforms.utils.tests.webtest_base import WebTestPyQueryMixin


def replace(mapping, **kwargs):
    assert kwargs
    d = mapping.copy()
    d.update(kwargs)
    return d


default_settings = dict(
    EMAIL_HOST="localhost",
    EMAIL_PORT=252525,
    EMAIL_HOST_USER="foo",
    EMAIL_HOST_PASSWORD="bar",
    EMAIL_USE_TLS=False,
    EMAIL_USE_SSL=False,
    EMAIL_TIMEOUT=10,
    EMAIL_SSL_KEYFILE=None,
    EMAIL_SSL_CERTFILE=None,
    DEFAULT_FROM_EMAIL="sender@bar.bazz",
)


class CheckSMTPSettingsFunctionTests(TestCase):
    @override_settings(**default_settings)
    def test_ok(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

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
            self.assertEqual(
                res.email_message.subject, _("Open Forms SMTP connection test")
            )

            name, args, kwargs = mock_smtp.method_calls.pop(0)
            self.assertEqual(name, "().login")
            self.assertEqual(("foo", "bar"), args)

            name, args, kwargs = mock_smtp.method_calls.pop(0)
            self.assertEqual(name, "().sendmail")
            self.assertEqual("sender@bar.bazz", args[0])
            self.assertEqual(["receiver@bar.bazz"], args[1])
            self.assertIn(b"Message-ID", args[2])
            self.assertIn(_("Open Forms SMTP connection test").encode("utf8"), args[2])

            name, args, kwargs = mock_smtp.method_calls.pop(0)
            self.assertEqual(name, "().quit")

    @override_settings(**default_settings)
    def test_init_value_error(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.side_effect = ValueError()
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [_("Cannot initialize email backend") % {"host": "localhost:252525"}],
            )
            self.assertIsInstance(res.exception, ValueError)

    @override_settings(**replace(default_settings, EMAIL_HOST=""))
    def test_init_bad_host_exception(self):
        res = check_smtp_settings("receiver@bar.bazz")

        self.assertEqual(res.success, False)
        self.assertEqual(res.feedback, [_("Missing required setting EMAIL_HOST")])
        self.assertIsNone(res.exception)

    @override_settings(
        **replace(default_settings, EMAIL_USE_TLS=True, EMAIL_USE_SSL=True)
    )
    def test_init_bad_host_exception(self):
        res = check_smtp_settings("receiver@bar.bazz")

        self.assertEqual(res.success, False)
        self.assertEqual(res.feedback, [_("Cannot initialize email backend")])
        self.assertIsInstance(res.exception, ValueError)

    @override_settings(**default_settings)
    def test_login_smtp_exception(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = smtplib.SMTPException()
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [_("Cannot connect to host %(host)s") % {"host": "localhost:252525"}],
            )
            self.assertIsInstance(res.exception, smtplib.SMTPException)

    @override_settings(**default_settings)
    def test_login_socket_error(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = socket.error()
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [_("Cannot connect to host %(host)s") % {"host": "localhost:252525"}],
            )
            self.assertIsInstance(res.exception, socket.error)

    @override_settings(**default_settings)
    def test_sendmail_smtp_exception(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.sendmail.side_effect = smtplib.SMTPException()
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [
                    _("Cannot send test message to %(email)s")
                    % {"email": "receiver@bar.bazz"}
                ],
            )
            self.assertIsInstance(res.exception, smtplib.SMTPException)

    @override_settings(**default_settings)
    def test_quit_smtp_exception(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.quit.side_effect = smtplib.SMTPException()
            res = check_smtp_settings("receiver@bar.bazz")
            mock_smtp.assert_called()

            self.assertEqual(res.success, False)
            self.assertEqual(
                res.feedback,
                [
                    _(
                        "Successfully sent test message to %(recipients)s, please check the mailbox."
                    )
                    % {"recipients": "receiver@bar.bazz"},
                    _("Cannot close connection to host %(host)s")
                    % {"host": "localhost:252525"},
                ],
            )
            self.assertIsInstance(res.exception, smtplib.SMTPException)


class CheckSMTPSettingsAdminViewTest(WebTestPyQueryMixin, WebTest):
    def test_requires_staff(self):
        url = reverse("admin_email_test")
        redirect_url = f"{settings.LOGIN_URL}?next={quote(url)}"

        with self.subTest("anon"):
            response = self.app.get(url, status=302)
            self.assertRedirects(response, redirect_url)

        with self.subTest("user"):
            user = UserFactory()
            self.app.set_user(user)
            response = self.app.get(url, status=302)
            self.assertRedirects(response, redirect_url)

        with self.subTest("staff"):
            user = StaffUserFactory()
            self.app.set_user(user)
            response = self.app.get(url, status=200)

    @override_settings(**default_settings)
    def test_run_check(self):
        with mock.patch("smtplib.SMTP", autospec=True) as mock_smtp:
            mock_smtp.return_value.login.side_effect = smtplib.SMTPException(
                "Foo Exception"
            )

            url = reverse("admin_email_test")
            user = StaffUserFactory()
            self.app.set_user(user)
            response = self.app.get(url, status=200)

            self.assertPyQueryExists(response, f"form[action='{url}']")
            self.assertPyQueryExists(response, f"input[name='recipient']")

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
                f"table[class='result-table'] tr td code:contains('Foo Exception')",
            )
