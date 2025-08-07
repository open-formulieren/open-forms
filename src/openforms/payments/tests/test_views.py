from decimal import Decimal
from unittest.mock import patch

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.test import TestCase, override_settings, tag
from django.test.client import RequestFactory
from django.urls import reverse

from rest_framework import status
from rest_framework.views import Request

from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin, Options, PaymentInfo
from ..constants import PaymentStatus
from ..models import SubmissionPayment
from ..registry import Registry
from .factories import SubmissionPaymentFactory


class PaymentError(Exception):
    pass


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    return_method = "GET"
    webhook_method = "POST"

    def start_payment(self, request, payment, options):
        return PaymentInfo(type="get", url="http://testserver/foo")

    def handle_return(self, request, payment, options):
        if request.GET.get("_error"):
            raise PaymentError("error triggered")
        return HttpResponseRedirect(payment.submission.form_url)

    def handle_webhook(self, request):
        return SubmissionPayment(id=None)


class ViewsTests(TestCase):
    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://allowed.foo"]
    )
    @patch("openforms.payments.views.on_post_submission_event")
    def test_views(self, on_post_submission_event_mock):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]
        bad_plugin = Plugin("bad_plugin")

        base_request = RequestFactory().get("/foo")

        registry_mock = patch("openforms.payments.views.register", new=register)
        registry_mock.start()
        self.addCleanup(registry_mock.stop)

        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
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

        payment.status = PaymentStatus.completed
        payment.save()

        # check the return view
        url = plugin.get_return_url(base_request, payment)
        self.assertRegex(url, r"^http://")

        with self.subTest("return ok"):
            on_post_submission_event_mock.reset_mock()

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(url)

            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 302)

            on_post_submission_event_mock.assert_called_once_with(
                submission.id, PostSubmissionEvents.on_payment_complete
            )

        with self.subTest("return bad method"):
            on_post_submission_event_mock.reset_mock()

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(url)

            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "GET")
            on_post_submission_event_mock.assert_not_called()

        with self.subTest("return bad plugin"):
            on_post_submission_event_mock.reset_mock()
            bad_payment = SubmissionPaymentFactory.for_backend("bad_plugin")
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)
            on_post_submission_event_mock.assert_not_called()

        with self.subTest("return bad redirect"):
            on_post_submission_event_mock.reset_mock()
            bad_payment = SubmissionPaymentFactory.for_backend(
                "plugin1", submission__form_url="http://bad.com/form"
            )
            bad_url = bad_plugin.get_return_url(base_request, bad_payment)

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "redirect not allowed")
            self.assertEqual(response.status_code, 400)
            on_post_submission_event_mock.assert_not_called()

        # check the webhook view
        url = plugin.get_webhook_url(base_request)
        self.assertRegex(url, r"^http://")

        with (
            self.subTest("webhook ok"),
            patch.object(plugin, "handle_webhook", return_value=payment),
        ):
            on_post_submission_event_mock.reset_mock()

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(url)

            self.assertEqual(response.content, b"")
            self.assertEqual(response.status_code, 200)

            on_post_submission_event_mock.assert_called_once_with(
                submission.id, PostSubmissionEvents.on_payment_complete
            )

        with self.subTest("webhook bad method"):
            on_post_submission_event_mock.reset_mock()

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(url)

            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
            on_post_submission_event_mock.assert_not_called()

        with self.subTest("webhook bad plugin"):
            on_post_submission_event_mock.reset_mock()
            bad_url = bad_plugin.get_webhook_url(base_request)

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.get(bad_url)

            self.assertEqual(response.data["detail"], "unknown plugin")
            self.assertEqual(response.status_code, 404)
            on_post_submission_event_mock.assert_not_called()

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://allowed.foo"]
    )
    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    @patch("openforms.payments.views.on_post_submission_event")
    def test_start_plugin_not_enabled(
        self, on_post_submission_event_mock, mock_get_solo
    ):
        register = Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]
        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"payments": {"plugin1": {"enabled": False}}}
        )
        registry_mock = patch("openforms.payments.views.register", new=register)
        registry_mock.start()
        self.addCleanup(registry_mock.stop)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
            form_url="http://allowed.foo/my-form",
        )
        base_request = RequestFactory().get("/foo")
        url = plugin.get_start_url(base_request, submission)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "parse_error")
        self.assertEqual(response.data["detail"], "plugin not enabled")
        self.assertFalse(SubmissionPayment.objects.exists())

    def test_start_with_no_payment_required(self):
        register = Registry()
        register("plugin1")(Plugin)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product=None,
        )
        start_url = reverse(
            "payments:start", kwargs={"uuid": submission.uuid, "plugin_id": "plugin1"}
        )

        with patch("openforms.payments.views.register", new=register):
            response = self.client.post(start_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_with_wrong_backend(self):
        register = Registry()
        register("plugin1")(Plugin)
        register("plugin2")(Plugin)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
        )
        start_url = reverse(
            "payments:start", kwargs={"uuid": submission.uuid, "plugin_id": "plugin2"}
        )

        with patch("openforms.payments.views.register", new=register):
            response = self.client.post(start_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_with_no_payment_required(self):
        register = Registry()
        register("plugin1")(Plugin)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product=None,
        )
        payment = SubmissionPaymentFactory.create(
            submission=submission, plugin_id="plugin1"
        )
        return_url = reverse("payments:return", kwargs={"uuid": payment.uuid})

        with patch("openforms.payments.views.register", new=register):
            response = self.client.get(return_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_with_wrong_backend(self):
        register = Registry()
        register("plugin1")(Plugin)
        register("plugin2")(Plugin)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
        )
        payment = SubmissionPaymentFactory.create(
            submission=submission, plugin_id="plugin2"
        )
        return_url = reverse("payments:return", kwargs={"uuid": payment.uuid})

        with patch("openforms.payments.views.register", new=register):
            response = self.client.get(return_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_crashes(self):
        register = Registry()
        register("plugin1")(Plugin)
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="plugin1",
        )
        payment = SubmissionPaymentFactory.create(
            submission=submission, plugin_id="plugin1"
        )
        return_url = reverse("payments:return", kwargs={"uuid": payment.uuid})

        with (
            patch("openforms.payments.views.register", new=register),
            self.assertRaises(PaymentError),
        ):
            self.client.get(return_url, {"_error": "1"})


class PaymentPlugin(BasePlugin):
    def handle_webhook(self, request):
        order_id = request.data["orderID"]
        payment = SubmissionPayment.objects.get(public_order_id=order_id)
        return payment

    def handle_return(
        self, request: HttpRequest, payment: "SubmissionPayment", options
    ) -> HttpResponse:
        return HttpResponseRedirect(payment.submission.form_url)


class BaseWebhookVerificationPaymentPlugin(BasePlugin):
    webhook_verification_header = "X-Custom-Verification"

    def handle_webhook(self, request: Request) -> SubmissionPayment | None:
        order_id = request.data["orderID"]
        status = request.data.get("status")
        payment = SubmissionPayment.objects.get(public_order_id=order_id)

        if not status:
            return payment

        payment.status = status
        payment.save(update_fields=("status",))
        return payment

    def handle_return(
        self, request: Request, payment: SubmissionPayment, options: Options
    ) -> HttpResponse:
        return HttpResponseRedirect(payment.submission.form_url)


class WebhookVerificationGetPaymentPlugin(BaseWebhookVerificationPaymentPlugin):
    webhook_method = "POST"
    webhook_verification_method = "GET"


class WebhookVerificationPostPaymentPlugin(BaseWebhookVerificationPaymentPlugin):
    webhook_verification_method = "POST"
    webhook_method = "POST"


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://allowed.foo"],
)
class WebhookReturnTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        register = Registry()
        register("payment-plugin")(PaymentPlugin)
        cls.plugin = register["payment-plugin"]
        cls.register = register

    def setUp(self):
        super().setUp()

        registry_mock = patch("openforms.payments.views.register", new=self.register)
        registry_mock.start()

        self.addCleanup(registry_mock.stop)

    @tag("gh-4052")
    def test_payment_cancelled_does_not_trigger_on_completion_in_webhook_endpoint(self):
        """
        The webhook can be called also in the case that the payment was cancelled/failed.
        In this case, we don't want to trigger the task:

            on_post_submission_event(
                <payment ID>, PostSubmissionEvents.on_payment_complete
            )
        """
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.failed
        )

        base_request = RequestFactory().get("/foo")

        webhook_url = self.plugin.get_webhook_url(base_request)

        with self.captureOnCommitCallbacks(execute=True):
            with patch(
                "openforms.payments.views.on_post_submission_event"
            ) as m_on_post_submission_event:
                response = self.client.post(
                    webhook_url, data={"orderID": payment.public_order_id}
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m_on_post_submission_event.assert_not_called()

    def test_successful_payment_triggers_on_completion_in_webhook_endpoint(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        base_request = RequestFactory().get("/foo")

        webhook_url = self.plugin.get_webhook_url(base_request)

        with self.captureOnCommitCallbacks(execute=True):
            with patch(
                "openforms.payments.views.on_post_submission_event"
            ) as m_on_post_submission_event:
                response = self.client.post(
                    webhook_url, data={"orderID": payment.public_order_id}
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Payment was successful, so 'transaction.on_commit' is called and triggers the on_post_submission_event
        m_on_post_submission_event.assert_called_once_with(
            submission.pk, PostSubmissionEvents.on_payment_complete
        )

    @tag("gh-4052")
    def test_payment_cancelled_does_not_trigger_on_completion_in_return_endpoint(self):
        """
        The return endpoint can be called also in the case that the payment was cancelled/failed.
        In this case, we don't want to trigger the task:

            on_post_submission_event(
                <payment ID>, PostSubmissionEvents.on_payment_complete
            )
        """
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.failed
        )

        base_request = RequestFactory().get("/foo")

        return_url = self.plugin.get_return_url(base_request, payment)

        with self.captureOnCommitCallbacks(execute=True):
            with patch(
                "openforms.payments.views.on_post_submission_event"
            ) as m_on_post_submission_event:
                response = self.client.get(return_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # Payment status is 'failed', so no 'transaction.on_commit' call that triggers the on_post_submission_event
        m_on_post_submission_event.assert_not_called()

    def test_successful_payment_triggers_on_completion_in_return_endpoint(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )

        base_request = RequestFactory().get("/foo")

        return_url = self.plugin.get_return_url(base_request, payment)

        with self.captureOnCommitCallbacks(execute=True):
            with patch(
                "openforms.payments.views.on_post_submission_event"
            ) as m_on_post_submission_event:
                response = self.client.get(return_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # Payment was successful, so 'transaction.on_commit' is called and triggers the on_post_submission_event
        m_on_post_submission_event.assert_called_once_with(
            submission.pk, PostSubmissionEvents.on_payment_complete
        )

    def test_verification_header_plugin(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.processing
        )
        base_request = RequestFactory().get("/foo")

        with self.subTest("Verification through the GET request method failed"):
            self.register("webhook-verification-get-plugin")(
                WebhookVerificationGetPaymentPlugin
            )
            plugin = self.register["webhook-verification-get-plugin"]
            webhook_url = plugin.get_webhook_url(base_request)

            with self.captureOnCommitCallbacks(execute=True):
                with patch(
                    "openforms.payments.views.on_post_submission_event"
                ) as m_on_post_submission_event:
                    response = self.client.get(
                        webhook_url,
                        headers={"X-Custom-Verification": "verification-code"},
                    )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.content, b"verification-code")

            m_on_post_submission_event.assert_not_called()

            payment.refresh_from_db()
            self.assertEqual(payment.status, PaymentStatus.processing)

        with self.subTest("Verification through the POST request method failed"):
            self.register("webhook-verification-post-plugin")(
                WebhookVerificationPostPaymentPlugin
            )
            plugin = self.register["webhook-verification-post-plugin"]
            webhook_url = plugin.get_webhook_url(base_request)

            with self.captureOnCommitCallbacks(execute=True):
                with patch(
                    "openforms.payments.views.on_post_submission_event"
                ) as m_on_post_submission_event:
                    response = self.client.post(
                        webhook_url,
                        headers={"X-Custom-Verification": "verification-code"},
                        content_type="text/plain; charset=utf-8",
                        data="",
                    )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.content, b"verification-code")

            m_on_post_submission_event.assert_not_called()

            payment.refresh_from_db()
            self.assertEqual(payment.status, PaymentStatus.processing)

    def test_payment_processed_with_verification_header_set(self):
        """
        Tests that the webhook is processed without triggering the verification
        header logic.
        """
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__product__price=Decimal("11.25"),
            form__payment_backend="payment-plugin",
            form_url="http://allowed.foo/my-form",
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.processing
        )

        self.register("webhook-verification-post-plugin")(
            WebhookVerificationPostPaymentPlugin
        )
        plugin = self.register["webhook-verification-post-plugin"]
        base_request = RequestFactory().get("/foo")
        webhook_url = plugin.get_webhook_url(base_request)

        with self.captureOnCommitCallbacks(execute=True):
            with patch(
                "openforms.payments.views.on_post_submission_event"
            ) as m_on_post_submission_event:
                response = self.client.post(
                    webhook_url,
                    headers={"X-Custom-Verification": "verification-code"},
                    data={
                        "orderID": payment.public_order_id,
                        "status": PaymentStatus.completed,
                    },
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Payment was successful, so 'transaction.on_commit' is called and triggers the on_post_submission_event
        m_on_post_submission_event.assert_called_once_with(
            submission.pk, PostSubmissionEvents.on_payment_complete
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
