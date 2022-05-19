"""
Test comleting a submitted form.

Completion of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend should perform total-form validation as part of this action.
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.forms.tests.factories import (
    FormFactory,
    FormPriceLogicFactory,
    FormStepFactory,
)

from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import SubmissionStep
from .factories import SubmissionFactory, SubmissionStepFactory
from .form_logic.factories import FormLogicFactory
from .mixins import SubmissionsMixin


@temp_private_root()
class SubmissionCompletionTests(SubmissionsMixin, APITestCase):
    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_required_steps_validated(self):
        step = FormStepFactory.create(optional=False)
        submission = SubmissionFactory.create(form=step.form)
        self._add_submission_to_session(submission)
        form_step_url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": step.form.uuid, "uuid": step.uuid},
        )
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        assert not SubmissionStep.objects.filter(
            submission=submission, form_step=step
        ).exists()

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "incompleteSteps": [
                    {"formStep": f"http://testserver{form_step_url}"},
                ],
                "submissionAllowed": SubmissionAllowedChoices.yes,
                "invalidPrefilledFields": [],
            },
        )

    @patch("openforms.submissions.api.viewsets.on_completion")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission(self, mock_on_completion):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        step1 = FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        step3 = FormStepFactory.create(form=form, optional=False)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"foo": "bar"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step3, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.post(endpoint)

        # TODO: in the future, a S-HMAC token based "statusUrl" will be returned which
        # needs to be polled by the frontend
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that the async celery task execution is scheduled
        mock_on_completion.assert_called_once_with(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission_in_maintenance_mode(self):
        form = FormFactory.create(maintenance_mode=True)
        step1 = FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=False)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"foo": "bar"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        # TODO: in the near future this will become HTTP_200_OK again, see
        # :meth:`test_complete_submission`
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

    def test_submit_form_with_not_applicable_step(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "driverId",
                    }
                ]
            },
        )
        form_step2_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": step2.uuid},
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "<": [
                    {"var": "age"},
                    18,
                ]
            },
            actions=[
                {
                    "form_step": f"http://example.com{form_step2_path}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"age": 16},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        submission.refresh_from_db()

        self.assertTrue(submission.is_completed)

    def test_submit_form_with_submission_disabled_with_overview(self):
        submission = SubmissionFactory.create(
            form__submission_allowed=SubmissionAllowedChoices.no_with_overview
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(
            response_data,
            {
                "incompleteSteps": [],
                "submissionAllowed": SubmissionAllowedChoices.no_with_overview,
                "invalidPrefilledFields": [],
            },
        )

    def test_submit_form_with_submission_disabled_without_overview(self):
        submission = SubmissionFactory.create(
            form__submission_allowed=SubmissionAllowedChoices.no_without_overview
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(
            response_data,
            {
                "incompleteSteps": [],
                "submissionAllowed": SubmissionAllowedChoices.no_without_overview,
                "invalidPrefilledFields": [],
            },
        )

    def test_form_auth_cleaned_after_completion(self):
        submission = SubmissionFactory.create(bsn="foo", kvk="foo", pseudo="foo")
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        # The auth details are cleaned by the signal handler
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            with capture_on_commit_callbacks(execute=True):
                self.client.post(endpoint)

        cleaned_session = self.client.session
        self.assertNotIn(FORM_AUTH_SESSION_KEY, cleaned_session)

        # assert that identifying attributs are hashed on completion
        submission.refresh_from_db()
        for attr in [AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo]:
            with self.subTest(attr=attr):
                value = getattr(submission, attr)
                self.assertTrue(
                    bool(value), "Expected a hashed value instead of empty value"
                )
                self.assertNotEqual(value, "foo")

    def test_prefilled_data_updated(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": True,
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(
            form=form, prefill_data={"test-prefill": {"surname": "Doe"}}
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"surname": "Doe-MODIFIED"},
        )

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error_data = response.json()

        self.assertEqual(1, len(error_data["invalidPrefilledFields"]))
        self.assertEqual("Surname", error_data["invalidPrefilledFields"][0])

    def test_prefilled_data_updated_not_disabled(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "surname",
                        "label": "Surname",
                        "prefill": {"plugin": "test-prefill", "attribute": "surname"},
                        "disabled": False,
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(
            form=form, prefill_data={"test-prefill": {"surname": "Doe"}}
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"surname": "Doe-MODIFIED"},
        )

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        # Since the prefilled field was not disabled, it is possible to modify it and the submission is valid
        self.assertEqual(status.HTTP_200_OK, response.status_code)


@temp_private_root()
class CSRFSubmissionCompletionTests(SubmissionsMixin, APITestCase):
    def setUp(self):
        # install a different client class with enforced CSRF checks
        self.client = self.client_class(enforce_csrf_checks=True)
        super().setUp()

    def test_can_complete_without_csrf_token_while_logged_in(self):
        """
        Assert that a CSRF token is not required if the user is authenticated.

        Regression test for #1627, where POST calls were blocked because of a missing
        CSRF token if the form was started BEFORE the user logged in to the admin
        area and the user logged in BEFORE copmleting/suspending the form (in another
        tab, for example).
        """
        user = UserFactory.create()
        self.client.force_login(
            user=user, backend="openforms.accounts.backends.UserModelEmailBackend"
        )
        submission = SubmissionFactory.from_data({"foo": "bar"})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@temp_private_root()
class SetSubmissionPriceOnCompletionTests(SubmissionsMixin, APITestCase):
    """
    Make assertions about price derivation on submission completion.
    """

    def test_no_product_no_price_rules(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__optional=True,
            form__product=None,
            form__payment_backend="demo",
        )
        with self.subTest(part="check data setup"):
            self.assertFalse(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertFalse(submission.payment_required)
        self.assertIsNone(submission.price)

    def test_no_product_linked_but_price_rules_set(self):
        """
        Test that payment is not required if no product is linked, even with price rules.
        """
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__optional=True,
            form__product=None,
            form__payment_backend="demo",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
        )
        FormPriceLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
            price=Decimal("9.6"),
        )
        with self.subTest(part="check data setup"):
            self.assertFalse(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertFalse(submission.payment_required)
        self.assertIsNone(submission.price)

    def test_use_product_price(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__optional=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("123.45"))

    def test_price_rules_specified(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__optional=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
        )
        FormPriceLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
            price=Decimal("51.15"),
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("51.15"))

    def test_price_rules_specified_but_no_match(self):
        """
        Assert that the product price is used as fallback.
        """
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__optional=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
        )
        FormPriceLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "test-key"}, "nottest"]},
            price=Decimal("51.15"),
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("123.45"))
