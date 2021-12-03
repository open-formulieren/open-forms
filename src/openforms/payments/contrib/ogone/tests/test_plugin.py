from decimal import Decimal

from django.test import RequestFactory, TestCase, override_settings

from furl import furl

from openforms.submissions.tests.factories import SubmissionFactory

from ....registry import register
from ....tests.factories import SubmissionPaymentFactory
from ..constants import OgoneStatus, PaymentStatus
from ..plugin import RETURN_ACTION_PARAM
from ..signing import calculate_sha_out
from .factories import OgoneMerchantFactory


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGINS=["http://foo.bar"]
)
class OgoneTests(TestCase):
    maxDiff = None

    def test_payment(self):
        merchant = OgoneMerchantFactory.create(
            pspid="psp123",
        )
        submission = SubmissionFactory.create(
            completed=True,
            form__slug="myform",
            form__payment_backend="ogone-legacy",
            form__payment_backend_options={"merchant_id": merchant.id},
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["ogone-legacy"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        # start url
        url = plugin.get_start_url(request, submission)

        # good
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["type"], "post")
        self.assertEqual(data["url"], merchant.endpoint)
        self.assertEqual(data["data"]["PSPID"], "psp123")
        self.assertEqual(data["data"]["CURRENCY"], "EUR")
        self.assertEqual(data["data"]["LANGUAGE"], "nl_NL")
        self.assertEqual(data["data"]["AMOUNT"], "1135")

        url = data["data"]["ACCEPTURL"]
        self.assertIn("action=accept", url)

        url = data["data"]["EXCEPTIONURL"]
        self.assertIn("action=exception", url)

        url = data["data"]["BACKURL"]
        self.assertIn("action=cancel", url)
        url = data["data"]["CANCELURL"]
        self.assertIn("action=cancel", url)
        url = data["data"]["DECLINEURL"]
        self.assertIn("action=cancel", url)

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "ogone-legacy")
        self.assertEqual(payment.status, PaymentStatus.started)

        # return url
        url = plugin.get_return_url(request, payment)

        ogone_params = {
            "ORDERID": payment.public_order_id,
            "STATUS": OgoneStatus.payment_requested,
            "GIROPAY_ACCOUNT_NUMBER": "1",  # hashed but not interesting
            "UNKNOWN_PARAM": "1",  # not hashed
        }
        ogone_params["SHASIGN"] = calculate_sha_out(
            ogone_params, merchant.sha_out_passphrase, merchant.hash_algorithm
        )

        return_url = furl(url)
        return_url.args.update(ogone_params)
        return_url.args[RETURN_ACTION_PARAM] = "accept"

        # good
        response = self.client.get(return_url.url)
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)

        # check if we end up back at the form
        self.assertRegex(response["Location"], r"^http://foo.bar")
        loc = furl(response["Location"])
        self.assertEqual(loc.args["of_payment_action"], "accept")
        self.assertEqual(loc.args["of_payment_status"], "completed")
        self.assertEqual(loc.args["of_payment_id"], str(payment.uuid))

        # check payment
        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)

        self.assertEqual(submission.payment_user_has_paid, True)

    def test_webhook(self):
        merchant = OgoneMerchantFactory.create(
            pspid="psp123",
        )
        submission = SubmissionFactory.create(
            completed=True,
            form__slug="myform",
            form__payment_backend="ogone-legacy",
            form__payment_backend_options={"merchant_id": merchant.id},
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["ogone-legacy"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        # start url
        url = plugin.get_webhook_url(request)

        # bad without data
        with self.subTest("bad call, no request data"):
            response = self.client.post(url)

            self.assertEqual(response.status_code, 400)

        # NOTE orderID is badly cased
        ogone_params = {
            "orderID": payment.public_order_id,
            "STATUS": OgoneStatus.payment_requested,
            "PAYID": 1234,
            "NCERROR": 0,
        }
        ogone_params["SHASIGN"] = calculate_sha_out(
            ogone_params, merchant.sha_out_passphrase, merchant.hash_algorithm
        )

        # good
        with self.subTest("valid call"):
            response = self.client.post(url, ogone_params)

            self.assertEqual(response.status_code, 200)

            submission.refresh_from_db()
            payment.refresh_from_db()
            self.assertEqual(payment.status, PaymentStatus.completed)
            self.assertEqual(submission.payment_user_has_paid, True)
