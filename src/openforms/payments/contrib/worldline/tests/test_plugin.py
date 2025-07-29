import json
import os
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode

from django.test import RequestFactory, override_settings

import requests
from bs4 import BeautifulSoup
from django_webtest import WebTest
from requests.exceptions import SSLError
from webtest import AppError

from openforms.payments.constants import PaymentStatus
from openforms.payments.contrib.worldline.constants import (
    HostedCheckoutStatus,
    PaymentStatus as _WorldlinePaymentStatus,
)
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ....registry import register

factory = RequestFactory()


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://foo.bar"],
    CSP_FORM_ACTION=["'self'"],
)
class WorldlinePluginTests(OFVCRMixin, WebTest):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def _get_vcr_kwargs(self, **kwargs):
        kwargs = super()._get_vcr_kwargs(**kwargs)
        kwargs["filter_headers"] = ["Authorization"]
        return kwargs

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.merchant = WorldlineMerchantFactory.create(
            pspid=os.getenv("WORLDLINE_PSPID", "maykinmedia"),
            api_key=os.getenv("WORLDLINE_API_KEY", "placeholder_api_key"),
            api_secret=os.getenv("WORLDLINE_API_SECRET", "placeholder_api_secret"),
        )

    def test_valid_payment(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": self.merchant.id},
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
        response = self.app.post(
            url,
            json.dumps({"merchant": self.merchant.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json

        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(self.merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        # parse the payment URL from within the initial Worldline page
        response = requests.get(data["url"])
        soup = BeautifulSoup(response.content)
        form = soup.select_one("form[name=redirectForm]")

        payment_url = form.attrs["action"]

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
                    "RETURNMAC": payment.plugin_options["returnmac"],
                    "hostedCheckoutId": payment.plugin_options["checkout_id"],
                },
                doseq=True,
            ),
        )

        response = self.app.get(redirect_url)

        submission.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertEqual(payment.provider_payment_id, "4367582396_0")
        self.assertEqual(submission.payment_user_has_paid, True)

    def test_completed_payment(self):
        """
        Verify that an already completed payment redirects the user to the
        completion page.

        Note that Worldline shows the succesful confirmation pages like the
        payment was done normally.
        """
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": self.merchant.id},
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
        response = self.app.post(
            url,
            json.dumps({"merchant": self.merchant.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json

        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(self.merchant.endpoint))

        payment = submission.payments.get()

        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        # simulate an already paid payment
        payment.status = PaymentStatus.completed
        payment.provider_payment_id = "foobar"
        payment.save()

        # parse the payment URL from within the initial Worldline page
        response = requests.get(data["url"])
        soup = BeautifulSoup(response.content)
        form = soup.select_one("form[name=redirectForm]")

        payment_url = form.attrs["action"]

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
                    "RETURNMAC": payment.plugin_options["returnmac"],
                    "hostedCheckoutId": payment.plugin_options["checkout_id"],
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
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": self.merchant.id},
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
        response = self.app.post(
            url,
            json.dumps({"merchant": self.merchant.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json

        self.assertEqual(data["type"], "get")
        self.assertEqual(data["data"], {})
        self.assertTrue(data["url"].startswith(self.merchant.endpoint))

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "worldline")
        self.assertEqual(payment.status, PaymentStatus.started)

        # parse the payment URL from within the initial Worldline page
        response = requests.get(data["url"])
        soup = BeautifulSoup(response.content)
        form = soup.select_one("form[name=redirectForm]")

        payment_url = form.attrs["action"]

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
                    "hostedCheckoutId": payment.plugin_options["checkout_id"],
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
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="worldline",
            form__payment_backend_options={"merchant": self.merchant.id},
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
            response = self.app.post(
                url,
                json.dumps({"merchant": self.merchant.id}),
                content_type="application/json",
            )

        self.assertIn(
            "Failed to retrieve redirect URL from payment provider",
            str(exception_manager.exception),
        )

        payment = submission.payments.get()

        self.assertEqual(payment.status, PaymentStatus.failed)
        self.assertEqual(submission.payment_user_has_paid, False)

    def test_finalized_status(self):
        payment = SubmissionPaymentFactory.create(status=PaymentStatus.started)
        plugin = register["worldline"]

        # regular apply
        plugin.apply_status(
            payment,
            _WorldlinePaymentStatus.paid,
            HostedCheckoutStatus.payment_created,
            "12345",
        )

        self.assertEqual(payment.status, PaymentStatus.completed)

        # set a final status registered
        payment.status = PaymentStatus.registered
        payment.save()

        # ignores when try to race/overwrite to completed again
        plugin.apply_status(
            payment,
            _WorldlinePaymentStatus.paid,
            HostedCheckoutStatus.payment_created,
            "12345",
        )

        # still registered
        self.assertEqual(payment.status, PaymentStatus.registered)

    def test_webhook(self):
        raise NotImplementedError

    def test_custom_com_and_title_attributes(self):
        raise NotImplementedError
