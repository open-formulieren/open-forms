import os
from decimal import Decimal
from urllib.parse import urlencode

from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests
from bs4 import BeautifulSoup, Tag
from django_webtest import WebTest
from requests.exceptions import SSLError
from vcr import VCR
from vcr.request import Request
from webtest import AppError

from openforms.payments.constants import PaymentStatus
from openforms.payments.models import SubmissionPayment
from openforms.payments.registry import register
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..constants import (
    PaymentStatus as _WorldlinePaymentStatus,
    WorldlineEndpoints,
)
from ..plugin import WorldlinePaymentPlugin
from .factories import (
    ReferencesFactory,
    WebhookEventRequestFactory,
    WorldlineMerchantFactory,
    WorldlineWebhookConfigurationFactory,
)
from .utils import generate_webhook_signature

factory = RequestFactory()

PSPID = os.getenv("WORLDLINE_PSPID", "pspid")


def _scrub_pspid(request: Request):
    if PSPID in request.uri:
        request.uri = request.uri.replace(PSPID, "pspid")
    return request


def pspid_matcher(request_one: Request, request_two: Request) -> bool:
    if request_one.uri == request_two.uri:
        return True

    url_format = f"{WorldlineEndpoints.test}/v2/pspid/hostedcheckouts"

    scrubbed_request = next(
        (request.uri == url_format for request in (request_one, request_two)), None
    )

    if not scrubbed_request:
        return False

    request = request_one if request_one != scrubbed_request else request_two

    if _scrub_pspid(request) == scrubbed_request:
        return True

    return False


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://foo.bar"],
    CSP_FORM_ACTION=["'self'"],
)
class WorldlinePluginTests(OFVCRMixin, WebTest):
    def _get_vcr_kwargs(self, **kwargs) -> dict:
        kwargs = super()._get_vcr_kwargs(**kwargs)
        kwargs.setdefault("filter_headers", [])
        kwargs["filter_headers"].append("Authorization")
        kwargs["before_record_request"] = _scrub_pspid
        return kwargs

    def _get_vcr(self, **kwargs) -> VCR:
        _vcr = super()._get_vcr(**kwargs)
        _vcr.register_matcher("pspid_matcher", pspid_matcher)
        _vcr.match_on = ["pspid_matcher"]
        return _vcr

    def test_valid_payment(self):
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.pspid},
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        assert submission.payment_required
        assert not submission.payment_user_has_paid

        plugin = register["worldline"]
        # we need an arbitrary request
        request = factory.get("/foo")
        # start url
        url = plugin.get_start_url(request, submission)

        # good
        response = self.app.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        with self.subTest(
            "Parse the payment URL from within the initial Worldline page"
        ):
            response = requests.get(data["url"])
            soup = BeautifulSoup(response.content, features="lxml")
            form = soup.select_one("form[name=redirectForm]")

            self.assertIsInstance(form, Tag)

            payment_url = form.attrs["action"]  # pyright: ignore[reportOptionalMemberAccess]
            # trigger the payment
            response = requests.get(
                payment_url,
                {
                    "ec": "",
                    "trxid": 0,
                },
            )

            self.assertNotIn(
                os.getenv("WORLDLINE_VARIANT_TITLE", "Custom page title"), response.text
            )

            # we need another arbitrary request
            request = factory.get("/foo")
            redirect_url = "{redirect_url}?{query_params}".format(
                redirect_url=plugin.get_return_url(request, payment),
                query_params=urlencode(
                    {
                        "RETURNMAC": payment.plugin_options["_checkoutDetails"][
                            "RETURNMAC"
                        ],
                        "hostedCheckoutId": payment.plugin_options["_checkoutDetails"][
                            "hostedCheckoutId"
                        ],
                    },
                    doseq=True,
                ),
            )

        response = self.app.get(redirect_url)

        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertTrue(payment.provider_payment_id)
        self.assertNotEqual(
            payment.provider_payment_id,
            payment.public_order_id,
            "Payment ID should not be equal to payment reference (merchant reference)",
        )
        self.assertEqual(submission.payment_user_has_paid, True)

    def test_completed_payment(self):
        """
        Verify that an already completed payment redirects the user to the
        completion page.

        Note that Worldline shows the succesful confirmation pages like the
        payment was done normally.
        """
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.pspid},
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
            completed=True,
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["worldline"]
        # we need an arbitrary request
        request = factory.get("/foo")
        # start url
        url = plugin.get_start_url(request, submission)

        # good
        response = self.app.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        # simulate an already paid payment
        payment.status = PaymentStatus.completed
        payment.provider_payment_id = "foobar"
        payment.public_order_id = "2025/OF-UPD749/1"
        payment.save()

        with self.subTest(
            "Parse the payment URL from within the initial Worldline page"
        ):
            response = requests.get(data["url"])
            soup = BeautifulSoup(response.content, features="lxml")
            form = soup.select_one("form[name=redirectForm]")

            self.assertIsInstance(form, Tag)

            payment_url = form.attrs["action"]  # pyright: ignore[reportOptionalMemberAccess]
            # trigger the payment
            requests.get(
                payment_url,
                {
                    "ec": "",
                    "trxid": 0,
                },
            )
            # we need another arbitrary request
            request = factory.get("/foo")
            redirect_url = "{redirect_url}?{query_params}".format(
                redirect_url=plugin.get_return_url(request, payment),
                query_params=urlencode(
                    {
                        "RETURNMAC": payment.plugin_options["_checkoutDetails"][
                            "RETURNMAC"
                        ],
                        "hostedCheckoutId": payment.plugin_options["_checkoutDetails"][
                            "hostedCheckoutId"
                        ],
                    },
                    doseq=True,
                ),
            )

        response = self.app.get(redirect_url)

        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertEqual(payment.provider_payment_id, "foobar")
        self.assertEqual(submission.payment_user_has_paid, True)

    def test_returnmac_mismatch(self):
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.pspid},
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["worldline"]
        # we need an arbitrary request
        request = factory.get("/foo")
        # start url
        url = plugin.get_start_url(request, submission)

        # good
        response = self.app.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        # match the merchant reference with what is shown in the cassette
        payment.public_order_id = "2025/OF-KUTK8B/5"
        payment.save()

        with self.subTest(
            "Parse the payment URL from within the initial Worldline page"
        ):
            response = requests.get(data["url"])
            soup = BeautifulSoup(response.content, features="lxml")
            form = soup.select_one("form[name=redirectForm]")

            self.assertIsInstance(form, Tag)

            payment_url = form.attrs["action"]  # pyright: ignore[reportOptionalMemberAccess]
            # trigger the payment
            requests.get(
                payment_url,
                {
                    "ec": "",
                    "trxid": 0,
                },
            )
            # we need another arbitrary request
            request = factory.get("/foo")
            redirect_url = "{redirect_url}?{query_params}".format(
                redirect_url=plugin.get_return_url(request, payment),
                query_params=urlencode(
                    {
                        "RETURNMAC": "foobar",
                        "hostedCheckoutId": payment.plugin_options["_checkoutDetails"][
                            "hostedCheckoutId"
                        ],
                    },
                    doseq=True,
                ),
            )

        with self.assertRaises(AppError) as exception_manager:
            response = self.app.get(redirect_url)

        self.assertIn(
            "Incorrect query parameters provided", str(exception_manager.exception)
        )

        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)
        self.assertEqual(payment.provider_payment_id, "")
        self.assertEqual(submission.payment_user_has_paid, False)

    def test_no_redirect_url(self):
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.pspid},
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["worldline"]
        # we need an arbitrary request
        request = factory.get("/foo")
        # start url
        url = plugin.get_start_url(request, submission)

        # good
        with (
            self.vcr_raises(SSLError),
            self.assertRaises(AppError) as exception_manager,
        ):
            self.app.post(url)

        self.assertIn(
            "Failed to retrieve redirect URL from payment provider",
            str(exception_manager.exception),
        )

        payment = submission.payments.get()
        self.assertEqual(payment.status, PaymentStatus.failed)
        self.assertEqual(submission.payment_user_has_paid, False)

    def test_invalid_checkout_status(self):
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        backend_options = {
            "merchant": merchant.pspid,
            "_checkoutDetails": {
                "RETURNMAC": "02ad7fa3-2c2b-4322-964c-c50081f0cb23",
                "hostedCheckoutId": "foobar",
            },
        }
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options=backend_options,
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )
        payment = SubmissionPayment.objects.create_for(
            submission, "worldline", backend_options, submission.price
        )

        request = factory.get("/foo")
        plugin = register["worldline"]
        redirect_url = "{redirect_url}?{query_params}".format(
            redirect_url=plugin.get_return_url(request, payment),
            query_params=urlencode(
                {
                    "RETURNMAC": payment.plugin_options["_checkoutDetails"][
                        "RETURNMAC"
                    ],
                    "hostedCheckoutId": payment.plugin_options["_checkoutDetails"][
                        "hostedCheckoutId"
                    ],
                },
                doseq=True,
            ),
        )

        with self.assertRaises(AppError) as exception_manager:
            self.app.get(redirect_url)

        self.assertIn(
            "Unable to retrieve checkout status", str(exception_manager.exception)
        )

        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)
        self.assertEqual(payment.provider_payment_id, "")
        self.assertEqual(submission.payment_user_has_paid, False)

    def test_finalized_status(self):
        payment = SubmissionPaymentFactory.create(status=PaymentStatus.started)
        plugin = register["worldline"]

        # regular apply
        plugin.apply_status(  # pyright: ignore[reportAttributeAccessIssue]
            payment,
            _WorldlinePaymentStatus.paid,
            "12345",
        )

        self.assertEqual(payment.status, PaymentStatus.completed)

        # set a final status registered
        payment.status = PaymentStatus.registered
        payment.save()

        # ignores when try to race/overwrite to completed again
        plugin.apply_status(  # pyright: ignore[reportAttributeAccessIssue]
            payment,
            _WorldlinePaymentStatus.paid,
            "12345",
        )

        # still registered
        self.assertEqual(payment.status, PaymentStatus.registered)

    def test_config_check(self):
        configuration_entries = list(WorldlinePaymentPlugin.iter_config_checks())  # pyright: ignore[reportAttributeAccessIssue]

        with self.subTest("Test config check without merchants"):
            self.assertEqual(len(configuration_entries), 2)

            merchant_entry = configuration_entries[0]
            webhook_entry = configuration_entries[1]

            self.assertEqual(
                merchant_entry.actions,
                [
                    (
                        _("Add merchant"),
                        reverse(
                            "admin:payments_worldline_worldlinemerchant_add",
                        ),
                    )
                ],
            )

            self.assertEqual(
                webhook_entry.actions,
                [
                    (
                        _("Configure webhooks"),
                        reverse(
                            "admin:payments_worldline_worldlinewebhookconfiguration_change",
                        ),
                    )
                ],
            )

        correct_merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
            label="Correct merchant",
        )
        incorrect_merchant = WorldlineMerchantFactory.create(
            pspid="dummy", api_key="foo", api_secret="bar", label="Incorrect merchant"
        )
        configuration_entries = list(WorldlinePaymentPlugin.iter_config_checks())  # pyright: ignore[reportAttributeAccessIssue]

        self.assertEqual(len(configuration_entries), 3)

        with self.subTest("Test correct entry", expected_merchant=correct_merchant):
            correct_entry = next(
                entry for entry in configuration_entries if entry.status
            )
            self.assertIn(correct_merchant.label, correct_entry.name)

        with self.subTest("Test incorrect entry", expected_merchant=incorrect_merchant):
            incorrect_entry = next(
                entry for entry in configuration_entries if not entry.status
            )
            self.assertIn(incorrect_merchant.label, incorrect_entry.name)

        with self.subTest("Test webhook entry"):
            self.assertEqual(
                configuration_entries[2].name, "Worldline webhook configuration"
            )

    def test_webhook_event(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, public_order_id="2025/OF-KUTK8B/5", provider_payment_id="12345"
        )

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="000000850010000188130000200001",  # should be ignored in this scenario
            payment__paymentOutput__references=ReferencesFactory(
                merchantReference="2025/OF-KUTK8B/5",
            ),
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.processing)
        self.assertEqual(payment.public_order_id, "2025/OF-KUTK8B/5")
        self.assertEqual(payment.provider_payment_id, "12345")

    def test_webhook_no_payment_id(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(
            submission, provider_payment_id=""
        )

        assert payment.status == PaymentStatus.started
        assert not payment.provider_payment_id

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="000000850010000188130000200001",
            payment__paymentOutput__references=ReferencesFactory(
                merchantReference=payment.public_order_id,
            ),
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.processing)
        self.assertEqual(payment.provider_payment_id, "000000850010000188130000200001")

    def test_webhook_event_completed_payment(self):
        """
        Tests that status mutations should not be possible for completed payments
        """
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.status = PaymentStatus.completed
        payment.public_order_id = "2025/OF-UPD749/1"
        payment.save(update_fields=("public_order_id", "status"))

        self.assertEqual(payment.provider_payment_id, "")

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="12345",
            payment__paymentOutput__references=ReferencesFactory(
                merchantReference="2025/OF-UPD749/1"
            ),
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertEqual(payment.provider_payment_id, "")

    def test_webbhook_api_version_mismatch(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.provider_payment_id = "12345"
        payment.save(update_fields=("provider_payment_id",))

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="12345",
            type="payment.pending_approval",
            apiVersion="v8",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "not compatible with SDK API", response_data["invalidParams"][0]["reason"]
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)

    def test_webbhook_incorrect_signature(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.provider_payment_id = "12345"
        payment.save(update_fields=("provider_payment_id",))

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="12345",
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": "foobar",
            },
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "failed to validate signature", response_data["invalidParams"][0]["reason"]
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)

    def test_webhook_unknown_signature(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.public_order_id = "2025/OF-UPD749/1"
        payment.save(update_fields=("provider_payment_id",))

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__paymentOutput__references=ReferencesFactory(
                merchantReference="2025/OF-UPD749/1"
            ),
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": "unknown",
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            "No secret key found for given value",
            response_data["invalidParams"][0]["reason"],
        )

    def test_webhook_unknown_payment(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.provider_payment_id = "12345"
        payment.save(update_fields=("provider_payment_id",))

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment__status=_WorldlinePaymentStatus.pending_approval,
            payment__id="unknown",
            type="payment.pending_approval",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        self.assertEqual(response.status_code, 404)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)

    def test_webhook_unknown_event_type(self):
        webhook_configuration = WorldlineWebhookConfigurationFactory.create()
        merchant = WorldlineMerchantFactory.create(pspid="psp123")
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        payment.provider_payment_id = "12345"
        payment.save(update_fields=("provider_payment_id",))

        assert payment.status == PaymentStatus.started

        plugin = register["worldline"]
        webhook_url = plugin.get_webhook_url(factory.get("/foo"))
        data = WebhookEventRequestFactory.build(
            payment={},
            type="foobar",
        )

        response = self.client.post(
            webhook_url,
            data=data,
            content_type="application/json",
            headers={
                "X-GCS-KeyId": webhook_configuration.webhook_key_id,
                "X-GCS-Signature": generate_webhook_signature(
                    webhook_configuration.webhook_key_secret, data
                ),
            },
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            "Unknown webhook event encountered",
            response_data["invalidParams"][0]["reason"],
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.started)

    def test_custom_descriptor_and_variant_attributes(self):
        merchant = WorldlineMerchantFactory.create(
            pspid=PSPID,
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={
                "merchant": merchant.pspid,
                "variant": os.getenv("WORLDLINE_VARIANT", "placeholder_variant"),
                "descriptor_template": "Descriptor: {{ public_reference }}",
            },
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        assert submission.payment_required
        assert not submission.payment_user_has_paid

        plugin = register["worldline"]
        # we need an arbitrary request
        request = factory.get("/foo")
        # start url
        url = plugin.get_start_url(request, submission)

        # good
        response = self.app.post(url)

        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        with self.subTest(
            "Parse the payment URL from within the initial Worldline page"
        ):
            response = requests.get(data["url"])
            soup = BeautifulSoup(response.content, features="lxml")
            form = soup.select_one("form[name=redirectForm]")

            self.assertIsInstance(form, Tag)

            payment_url = form.attrs["action"]  # pyright: ignore[reportOptionalMemberAccess]
            # trigger the payment
            response = requests.get(
                payment_url,
                {
                    "ec": "",
                    "trxid": 0,
                },
            )

            self.assertIn(
                os.getenv("WORLDLINE_VARIANT_TITLE", "Custom page title"), response.text
            )

            # we need another arbitrary request
            request = factory.get("/foo")
            redirect_url = "{redirect_url}?{query_params}".format(
                redirect_url=plugin.get_return_url(request, payment),
                query_params=urlencode(
                    {
                        "RETURNMAC": payment.plugin_options["_checkoutDetails"][
                            "RETURNMAC"
                        ],
                        "hostedCheckoutId": payment.plugin_options["_checkoutDetails"][
                            "hostedCheckoutId"
                        ],
                    },
                    doseq=True,
                ),
            )

        response = self.app.get(redirect_url)

        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertTrue(payment.provider_payment_id)
        self.assertEqual(submission.payment_user_has_paid, True)
