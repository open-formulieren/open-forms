import json
from decimal import Decimal
from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve

from furl import furl

from openforms.submissions.tests.factories import SubmissionFactory

from ....constants import PaymentStatus
from ....registry import register


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://foo.bar"],
    CSP_FORM_ACTION=["'self'"],
)
class DemoPaymentTests(TestCase):
    maxDiff = None

    def test_payment(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__slug="myform",
            form__payment_backend="demo",
            form__product__price=Decimal("11.35"),
            form_url="http://foo.bar",
        )

        self.assertEqual(submission.payment_required, True)
        self.assertEqual(submission.payment_user_has_paid, False)

        plugin = register["demo"]

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        # start url
        url = plugin.get_start_url(request, submission)

        # good
        with patch("openforms.payments.base.BasePlugin.is_enabled", return_value=True):
            response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        payment = submission.payments.get()
        self.assertEqual(payment.plugin_id, "demo")
        self.assertEqual(payment.status, PaymentStatus.started)

        # return url
        url = plugin.get_return_url(request, payment)

        # good
        response = self.client.get(url)
        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)

        # check if we end up back at the form
        self.assertRegex(response["Location"], r"^http://foo.bar")

        loc = furl(response["Location"])

        self.assertEqual(loc.args["_of_action"], "payment")
        self.assertIn("_of_action_params", loc.args)

        params = json.loads(loc.args["_of_action_params"])

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

        self.assertEqual(submission.payment_user_has_paid, True)
