import os
from decimal import Decimal
from unittest import expectedFailure
from urllib.parse import urlencode

from django.test import RequestFactory, override_settings

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
    WorldlineMerchantFactory,
)

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
        self.assertTrue(payment.provider_payment_id)
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
        self.assertTrue(payment.provider_payment_id)
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

        self.assertEqual(len(configuration_entries), 2)

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

    @expectedFailure
    def test_webhook(self):
        raise NotImplementedError

    @expectedFailure
    def test_custom_com_and_title_attributes(self):
        raise NotImplementedError
