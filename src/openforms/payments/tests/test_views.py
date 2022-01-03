from decimal import Decimal
from unittest.mock import patch

from django.http import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from django_capture_on_commit_callbacks import capture_on_commit_callbacks

from openforms.config.models import GlobalConfiguration
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin, PaymentInfo
from ..models import SubmissionPayment
from ..registry import Registry
from .factories import SubmissionPaymentFactory


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    return_method = "GET"
    webhook_method = "POST"

    def start_payment(self, request, payment):
        return PaymentInfo(type="get", url="http://testserver/foo")

    def handle_return(self, request, payment):
        return HttpResponseRedirect(payment.submission.form_url)

    def handle_webhook(self, request):
        return None


class ViewsTests(TestCase):
    def setUp(self):
        super().setUp()

        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {}
        config.save()

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://allowed.foo"]
    )
    @patch("openforms.payments.views.update_submission_payment_status.delay")
    def test_views(self, update_payments_mock):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]
        bad_plugin = Plugin("bad_plugin")

        base_request = RequestFactory().get("/foo")

        registry_mock = patch("openforms.payments.views.register", new=register)
        registry_mock.start()
        self.addCleanup(registry_mock.stop)

        submission = SubmissionFactory.create(
            completed=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
            form_url="http://allowed.foo/my-form",
        )
        self.assertTrue(submission.payment_required)

        # check the start url
        url = plugin.get_start_url(base_request, submission)
        self.assertRegex(url, r"^http://")

        with self.subTest("start ok"):
            response = self.client.post(url)
            self.assertEqual(
                response.data,
                {
                    "url": "http://testserver/foo",
                    "type": "get",
                    "data": None,
                },
            )
            self.assertEqual(response.status_code, 200)

            # keep this
            payment = SubmissionPayment.objects.get()

        with self.subTest("start bad plugin"):
            bad_url = bad_plugin.get_start_url(base_request, submission)
            response = self.client.post(bad_url)
            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)

        # check the return view
        url = plugin.get_return_url(base_request, payment)
        self.assertRegex(url, r"^http://")

        with self.subTest("return ok"):
            update_payments_mock.reset_mock()

            with capture_on_commit_callbacks(execute=True):
                response = self.client.get(url)

            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

            update_payments_mock.assert_called_once_with(submission.id)

        with self.subTest("return bad method"):
            update_payments_mock.reset_mock()

            with capture_on_commit_callbacks(execute=True):
                response = self.client.post(url)

            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")
            update_payments_mock.assert_not_called()

        with self.subTest("return bad plugin"):
            update_payments_mock.reset_mock()
            bad_payment = SubmissionPaymentFactory.for_backend("bad_plugin")
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)

            with capture_on_commit_callbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)
            update_payments_mock.assert_not_called()

        with self.subTest("return bad redirect"):
            update_payments_mock.reset_mock()
            bad_payment = SubmissionPaymentFactory.for_backend(
                "plugin1", submission__form_url="http://bad.com/form"
            )
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)

            with capture_on_commit_callbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "redirect not allowed")
            self.assertEqual(response.status_code, 400)
            update_payments_mock.assert_not_called()

        # check the webhook view
        url = plugin.get_webhook_url(base_request)
        self.assertRegex(url, r"^http://")

        with self.subTest("webhook ok"), patch.object(
            plugin, "handle_webhook", return_value=payment
        ):
            update_payments_mock.reset_mock()

            with capture_on_commit_callbacks(execute=True):
                response = self.client.post(url)

            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 200)

            update_payments_mock.assert_called_once_with(submission.id)

        with self.subTest("webhook bad method"):
            update_payments_mock.reset_mock()

            with capture_on_commit_callbacks(execute=True):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
            update_payments_mock.assert_not_called()

        with self.subTest("webhook bad plugin"):
            update_payments_mock.reset_mock()
            bad_url = bad_plugin.get_webhook_url(base_request)

            with capture_on_commit_callbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)
            update_payments_mock.assert_not_called()

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://allowed.foo"]
    )
    @patch("openforms.payments.views.update_submission_payment_status.delay")
    def test_start_plugin_not_enabled(self, update_payments_mock):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {"payments": {"plugin1": {"enabled": False}}}
        config.save()

        base_request = RequestFactory().get("/foo")

        registry_mock = patch("openforms.payments.views.register", new=register)
        registry_mock.start()
        self.addCleanup(registry_mock.stop)

        submission = SubmissionFactory.create(
            completed=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
            form_url="http://allowed.foo/my-form",
        )
        self.assertTrue(submission.payment_required)

        # check the start url
        url = plugin.get_start_url(base_request, submission)
        self.assertRegex(url, r"^http://")

        with self.subTest("start ok"):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data["code"], "parse_error")
            self.assertEqual(response.data["detail"], "plugin not enabled")

        self.assertFalse(SubmissionPayment.objects.exists())
