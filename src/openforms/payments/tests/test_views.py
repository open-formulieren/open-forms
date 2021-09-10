from decimal import Decimal
from unittest.mock import patch
from urllib.parse import quote

from django.http import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from openforms.payments.models import SubmissionPayment
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin, PaymentInfo
from ..registry import Registry


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    return_method = "GET"
    webhook_method = "POST"

    def start_payment(self, request, payment):
        return PaymentInfo(type="get", url="http://testserver/foo")

    def handle_return(self, request, payment):
        return HttpResponseRedirect(payment.form_url)

    def handle_webhook(self, request):
        return None


class ViewsTests(TestCase):
    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
    )
    @patch("openforms.payments.views.update_submission_payment_registration")
    def test_views(self, update_payments_mock):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]
        bad_plugin = Plugin("bad_plugin")

        base_request = RequestFactory().get("/foo")

        next_url_enc = quote("http://foo.bar")
        bad_url_enc = quote("http://buzz.bazz")

        registry_mock = patch("openforms.payments.views.register", new=register)
        registry_mock.start()
        self.addCleanup(registry_mock.stop)

        submission = SubmissionFactory.create(
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
        )
        self.assertTrue(submission.payment_required)

        # check the start url
        url = plugin.get_start_url(base_request, submission)
        self.assertRegex(url, r"^http://")

        with self.subTest("start ok"):
            response = self.client.post(f"{url}?next={next_url_enc}")
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

        with self.subTest("start missing next"):
            response = self.client.post(url)
            self.assertEqual(response.data["detail"], "missing 'next' parameter")
            self.assertEqual(response.status_code, 400)

        with self.subTest("start bad plugin"):
            bad_url = bad_plugin.get_start_url(base_request, submission)
            response = self.client.post(f"{bad_url}?next={next_url_enc}")
            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)

        with self.subTest("start bad redirect"):
            response = self.client.post(f"{url}?next={bad_url_enc}")
            self.assertEqual(response.data["detail"], "redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the return view
        url = plugin.get_return_url(base_request, payment)
        self.assertRegex(url, r"^http://")

        with self.subTest("return ok"):
            update_payments_mock.reset_mock()

            response = self.client.get(url)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

            update_payments_mock.assert_called_once_with(submission)

        with self.subTest("return bad method"):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")

        with self.subTest("return bad plugin"):
            bad_payment = SubmissionPaymentFactory.for_backend(
                "bad_plugin", form_url="http://foo.bar"
            )
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)
            response = self.client.get(bad_url)
            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)

        with self.subTest("return bad redirect"):
            bad_payment = SubmissionPaymentFactory.for_backend(
                "plugin1", form_url="http://buzz.bazz"
            )
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)
            response = self.client.get(bad_url)
            self.assertEqual(response.data["detail"], "redirect not allowed")
            self.assertEqual(response.status_code, 400)

        # check the webhook view
        url = plugin.get_webhook_url(base_request)
        self.assertRegex(url, r"^http://")

        with self.subTest("webhook ok"), patch.object(
            plugin, "handle_webhook", return_value=payment
        ):
            update_payments_mock.reset_mock()

            response = self.client.post(url)
            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 200)

            update_payments_mock.assert_called_once_with(submission)

        with self.subTest("webhook bad method"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")

        with self.subTest("webhook bad plugin"):
            bad_url = bad_plugin.get_webhook_url(base_request)
            response = self.client.get(bad_url)
            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)
