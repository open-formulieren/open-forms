import json
from decimal import Decimal

from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve

from furl import furl

from openforms.submissions.tests.factories import SubmissionFactory

from ....registry import register
from ....tests.factories import SubmissionPaymentFactory
from ..constants import OgoneStatus, PaymentStatus
from ..plugin import RETURN_ACTION_PARAM, OgoneLegacyPaymentPlugin
from ..signing import calculate_sha_out
from ..typing import PaymentOptions
from .factories import OgoneMerchantFactory

factory = RequestFactory()


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://foo.bar"],
    CSP_FORM_ACTION=["'self'"],
)
class OgoneTests(TestCase):
    maxDiff = None

    def test_payment(self):
        merchant = OgoneMerchantFactory.create(
            pspid="psp123",
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
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
            "PAYID": "4249708957",
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

        self.assertEqual(loc.args["_of_action"], "payment")
        self.assertIn("_of_action_params", loc.args)

        params = json.loads(loc.args["_of_action_params"])

        self.assertEqual(params["of_payment_action"], "accept")
        self.assertEqual(params["of_payment_status"], "completed")
        self.assertEqual(params["of_payment_id"], str(payment.uuid))
        self.assertIn("of_submission_status", params)

        status_url = params["of_submission_status"]
        match = resolve(furl(status_url).path)

        self.assertEqual(match.view_name, "api:submission-status")

        # check payment
        submission.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.completed)
        self.assertEqual(payment.provider_payment_id, "4249708957")

        self.assertEqual(submission.payment_user_has_paid, True)

    def test_webhook(self):
        merchant = OgoneMerchantFactory.create(
            pspid="psp123",
        )
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
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
        request = factory.get("/foo")

        # start url
        url = plugin.get_webhook_url(request)

        # bad without orderID
        with self.subTest("bad call, missing orderID"):
            response = self.client.post(url)

            self.assertEqual(response.status_code, 400)

        # bad without PAYID
        with self.subTest("bad call, missing PAYID"):
            response = self.client.post(url, {"orderID": payment.public_order_id})

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

    def test_apply_status(self):
        payment = SubmissionPaymentFactory.create(status=PaymentStatus.started)
        plugin = register["ogone-legacy"]

        # regular apply
        plugin.apply_status(payment, OgoneStatus.payment_requested, "12345")
        self.assertEqual(payment.status, PaymentStatus.completed)

        # set a final status registered
        payment.status = PaymentStatus.registered
        payment.save()

        # ignores when try to race/overwrite to completed again
        plugin.apply_status(payment, OgoneStatus.payment_requested, "12345")
        # still registered
        self.assertEqual(payment.status, PaymentStatus.registered)

    def test_custom_com_and_title_attributes(self):
        merchant = OgoneMerchantFactory.create()
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "type": "textfield",
                    "key": "inputField",
                    "label": "Some text input",
                }
            ],
            submitted_data={"inputField": "bröther gib lämp"},
            with_public_registration_reference=True,
            public_registration_reference="OF-1234",
            form__payment_backend="ogone-legacy",
            form__product__price=Decimal("11.35"),
        )
        payment = SubmissionPaymentFactory.for_submission(submission)
        assert submission.payment_required
        assert not submission.payment_user_has_paid
        plugin = OgoneLegacyPaymentPlugin("ogone-legacy")
        options: PaymentOptions = {
            "merchant_id": merchant,
            # No length limit applies to the title
            "title_template": r"Input: {{ inputField }} - ref: {{ public_reference }}",
            # result must be capped at 100 chars, see
            # https://support.legacy.worldline-solutions.com/en/help/parameter-cookbook
            "com_template": r"Input: {{ inputField }} - ref: {{ public_reference }} "
            + "A" * 90,
        }
        # we need an arbitrary request
        request = factory.get("/foo")

        payment_info = plugin.start_payment(request, payment, options)

        assert payment_info.data is not None
        self.assertEqual(
            payment_info.data["TITLE"], "Input: bröther gib lämp - ref: OF-1234"
        )
        self.assertEqual(
            payment_info.data["COM"],
            "Input: bröther gib lämp - ref: OF-1234 "
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        )
