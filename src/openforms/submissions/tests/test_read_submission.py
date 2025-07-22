"""
All state is managed on the backend - it's the definitive source of truth which also
makes resuming possible across devices (if you have a "magic link").

This information drives the frontend/navigation.
"""

from decimal import Decimal

from django.test import tag

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.variables.constants import FormVariableDataTypes

from ..utils import persist_user_defined_variables
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)
from .mixins import SubmissionsMixin


class SubmissionReadTests(SubmissionsMixin, APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step = FormStepFactory.create(
            form=cls.form, form_definition__name="Select product"
        )
        cls.submission = SubmissionFactory.create(
            form=cls.form, privacy_policy_accepted=True
        )
        cls.endpoint = reverse(
            "api:submission-detail", kwargs={"uuid": cls.submission.uuid}
        )

    def test_invalid_submission_id(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_api.txt"
            ).exists()
        )

    def test_retrieve_submission_nothing_submitted(self):
        self._add_submission_to_session(self.submission)
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": self.form.uuid})
        form_step_path = reverse(
            "api:form-steps-detail",
            kwargs={
                "form_uuid_or_slug": self.form.uuid,
                "uuid": self.step.uuid,
            },
        )
        submission_step_path = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step.uuid,
            },
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            {
                "id": str(self.submission.uuid),
                "url": f"http://testserver{self.endpoint}",
                "form": f"http://testserver{form_path}",
                "formUrl": "",
                "initialDataReference": "",
                "steps": [
                    {
                        "id": str(self.step.uuid),
                        "url": f"http://testserver{submission_step_path}",
                        "formStep": f"http://testserver{form_step_path}",
                        "isApplicable": True,
                        "completed": False,
                        "name": "Select product",
                        "canSubmit": True,
                    }
                ],
                "submissionAllowed": SubmissionAllowedChoices.yes,
                "payment": {
                    "isRequired": False,
                    "hasPaid": False,
                    "amount": None,
                },
                "isAuthenticated": False,
            },
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_api.txt"
            ).count(),
            1,
        )

    def test_submission_is_authenticated(self):
        self._add_submission_to_session(self.submission)

        with self.subTest("no"):
            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.json()["isAuthenticated"])

        with self.subTest("yes"):
            AuthInfoFactory.create(submission=self.submission)

            response = self.client.get(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.json()["isAuthenticated"])


class SubmissionReadPaymentInformationTests(SubmissionsMixin, APITestCase):
    def test_submission_payment_information_no_payment_required(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            form__product=None,
            form__payment_backend="demo",
        )
        submission.calculate_price()
        with self.subTest(part="check data setup"):
            self.assertFalse(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["payment"],
            {
                "isRequired": False,
                "amount": None,
                "hasPaid": False,
            },
        )

    def test_submission_payment_information_uses_product_price(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
        )
        submission.calculate_price()
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["payment"],
            {
                "isRequired": True,
                "amount": "123.45",
                "hasPaid": False,
            },
        )

    def test_submission_payment_information_uses_logic_rules(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_logic__price_variable="totalPrice",
            form__price_logic__price_value=51.15,
            form__price_logic__json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
        )
        FormVariableFactory.create(
            key="test-key",
            form=submission.form,
            form_definition=submission.form.formstep_set.get().form_definition,
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
        )
        persist_user_defined_variables(submission)
        submission.calculate_price()
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["payment"],
            {
                "isRequired": True,
                "amount": "51.15",
                "hasPaid": False,
            },
        )

    def test_submission_payment_information_uses_price_variable(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_variable_key="",
        )
        FormVariableFactory.create(
            user_defined=True,
            key="calculatedPrice",
            form=submission.form,
            data_type=FormVariableDataTypes.float,
            initial_value=420.69,
        )
        submission.form.price_variable_key = "calculatedPrice"
        submission.form.save()
        submission.refresh_from_db()
        submission.calculate_price()
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["payment"],
            {
                "isRequired": True,
                "amount": "420.69",
                "hasPaid": False,
            },
        )

    @tag("gh-2709")
    def test_submission_payment_with_logic_using_user_defined_variables(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"type": "number", "key": "triggerComponent"}],
            submitted_data={"triggerComponent": 1},
            form__product__price=Decimal("10"),
            form__payment_backend="demo",
            form__price_logic__price_variable="totalPrice",
            form__price_logic__json_logic_trigger={
                "==": [{"var": "userDefinedVar"}, 2]
            },
            form__price_logic__price_value=20,
        )
        SubmissionValueVariableFactory.create(
            key="userDefinedVar",
            submission=submission,
            data_type=FormVariableDataTypes.int,
            form_variable__user_defined=True,
            value=0,
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "triggerComponent"}, 1]},
            actions=[
                {
                    "variable": "userDefinedVar",
                    "action": {"type": "variable", "value": 2},
                }
            ],
            order=1,
        )
        persist_user_defined_variables(submission)
        assert submission.payment_required
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["payment"],
            {
                "isRequired": True,
                "amount": "20.00",
                "hasPaid": False,
            },
        )
