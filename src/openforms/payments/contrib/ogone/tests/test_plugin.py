from urllib.parse import quote

from django.test import RequestFactory, TestCase, override_settings

from furl import furl

from openforms.payments.constants import PaymentStatus
from openforms.payments.contrib.ogone.constants import OgoneStatus
from openforms.payments.contrib.ogone.plugin import RETURN_ACTION_PARAM
from openforms.payments.contrib.ogone.signing import calculate_shasign
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.payments.registry import register
from openforms.submissions.tests.factories import SubmissionFactory


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
            form__slug="myform",
            form__payment_backend="ogone-legacy",
            form__payment_backend_options={"merchant_id": merchant.id},
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_completed, False)

        plugin = register["ogone-legacy"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        # start url
        url = plugin.get_start_url(request, submission)
        next_url = quote("http://foo.bar")

        # bad without ?next=
        response = self.client.post(url)
        self.assertEqual(response.content, b"missing 'next' parameter")
        self.assertEqual(response.status_code, 400)

        # good
        response = self.client.post(f"{url}?next={next_url}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["type"], "post")
        self.assertEqual(data["url"], merchant.endpoint)
        self.assertEqual(data["data"]["PSPID"], "psp123")
        self.assertEqual(data["data"]["CURRENCY"], "EUR")
        self.assertEqual(data["data"]["LANGUAGE"], "nl_NL")
        self.assertEqual(data["data"]["AMOUNT"], "1000")

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
            "ORDERID": payment.order_id,
            "STATUS": OgoneStatus.payment_requested,
        }
        ogone_params["SHASIGN"] = calculate_shasign(
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

        self.assertEqual(submission.payment_completed, True)
