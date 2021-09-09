from decimal import Decimal
from unittest.mock import patch
from urllib.parse import quote

from django.http import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from ...forms.tests.factories import FormStepFactory
from ...plugins.constants import UNIQUE_ID_MAX_LENGTH
from ...submissions.tests.factories import SubmissionFactory
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
        return HttpResponseRedirect(payment.form_url)

    def handle_webhook(self, request):
        return None


class FailingPlugin(BasePlugin):
    verbose_name = "some human readable label"

    def start_payment(self, request, payment):
        raise Exception("start")

    def handle_return(self, request, payment):
        raise Exception("return")

    def handle_webhook(self, request):
        raise Exception("webhook")


class RegistryTests(TestCase):
    def test_register_function(self):
        register = Registry()

        register("plugin1")(Plugin)

        plugin = register["plugin1"]

        self.assertIsInstance(plugin, Plugin)
        self.assertEqual(plugin.identifier, "plugin1")
        self.assertEqual(plugin.verbose_name, "some human readable label")
        self.assertEqual(plugin.get_label(), plugin.verbose_name)

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin")(Plugin)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry",
        ):
            register("plugin")(Plugin)

    def test_long_identifier(self):
        register = Registry()
        long_identifier = "x" * (UNIQUE_ID_MAX_LENGTH + 1)

        with self.assertRaisesMessage(
            ValueError,
            f"The unique identifier '{long_identifier}' is longer then {UNIQUE_ID_MAX_LENGTH} characters.",
        ):
            register(long_identifier)(Plugin)

    def test_get_choices(self):
        register = Registry()
        register("plugin1")(Plugin)

        choices = register.get_choices()
        self.assertEqual(choices, [("plugin1", "some human readable label")])

    def test_get_options(self):
        register = Registry()
        register("plugin1")(Plugin)

        factory = RequestFactory()
        request = factory.get("/xyz")
        step = FormStepFactory(
            form__slug="myform",
            form__payment_backend="plugin1",
            form__payment_backend_options={"foo": 1},
        )
        form = step.form
        self.assertEqual(form.payment_backend, "plugin1")

        options = register.get_options(request, form)
        self.assertEqual(len(options), 1)

        option = options[0]
        self.assertEqual(option.identifier, "plugin1")
        self.assertEqual(option.label, "some human readable label")


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
