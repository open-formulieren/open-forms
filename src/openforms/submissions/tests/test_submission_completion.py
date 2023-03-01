"""
Test comleting a submitted form.

Completion of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend should perform total-form validation as part of this action.
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import override_settings, tag
from django.utils import timezone

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import SubmissionAllowedChoices
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormPriceLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import SubmissionStep
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)
from .mixins import SubmissionsMixin


@temp_private_root()
class SubmissionCompletionTests(SubmissionsMixin, APITestCase):
    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(LANGUAGE_CODE="en")
    def test_all_required_steps_validated(self):
        step = FormStepFactory.create(form_definition__name="Personal Details")
        submission = SubmissionFactory.create(form=step.form)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        assert not SubmissionStep.objects.filter(
            submission=submission, form_step=step
        ).exists()

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["invalidParams"],
            [
                {
                    "name": "incompleteSteps",
                    "code": "max_length",
                    "reason": "Not all applicable steps have been completed: ['Personal Details']",
                }
            ],
        )

    @patch("openforms.submissions.api.viewsets.on_completion")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission(self, mock_on_completion):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        step1 = FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"foo": "bar"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that the async celery task execution is scheduled
        mock_on_completion.assert_called_once_with(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())
        self.assertTrue(submission.privacy_policy_accepted)

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])

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
                    "form_step_uuid": f"{step2.uuid}",
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

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        submission.refresh_from_db()

        self.assertTrue(submission.is_completed)

    @override_settings(LANGUAGE_CODE="en")
    def test_submit_form_with_submission_disabled_with_overview(self):
        submission = SubmissionFactory.create(
            form__submission_allowed=SubmissionAllowedChoices.no_with_overview,
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(
            response_data["invalidParams"],
            [
                {
                    "name": "submissionAllowed",
                    "code": "invalid",
                    "reason": "Submission of this form is not allowed.",
                }
            ],
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_submit_form_with_submission_disabled_without_overview(self):
        submission = SubmissionFactory.create(
            form__submission_allowed=SubmissionAllowedChoices.no_without_overview,
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(
            response_data["invalidParams"],
            [
                {
                    "name": "submissionAllowed",
                    "code": "invalid",
                    "reason": "Submission of this form is not allowed.",
                }
            ],
        )

    def test_form_auth_cleaned_after_completion(self):
        submission = SubmissionFactory.create(auth_info__value="foo")
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
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(endpoint, {"privacy_policy_accepted": True})

        cleaned_session = self.client.session
        self.assertNotIn(FORM_AUTH_SESSION_KEY, cleaned_session)

        # assert that identifying attributs are hashed on completion
        submission.refresh_from_db()

        value = submission.auth_info.value
        self.assertTrue(
            bool(submission.auth_info.value),
            "Expected a hashed value instead of empty value",
        )
        self.assertNotEqual(value, "foo")

    def test_privacy_policy_accepted(self):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        form_step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        with patch(
            "openforms.submissions.api.validation.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(ask_privacy_consent=True),
        ):
            response = self.client.post(
                reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
                data={"privacy_policy_accepted": True},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(LANGUAGE_CODE="en")
    def test_submission_privacy_policy_not_accepted(self):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        form_step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        response = self.client.post(
            reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
            data={"privacy_policy_accepted": False},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["invalidParams"],
            [
                {
                    "name": "privacyPolicyAccepted",
                    "code": "invalid",
                    "reason": "Privacy policy must be accepted before completing submission.",
                }
            ],
        )

    def test_submission_privacy_policy_not_accepted_but_not_required(self):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        form_step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        with patch(
            "openforms.submissions.api.validation.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(ask_privacy_consent=False),
        ):
            response = self.client.post(
                reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
                data={"privacy_policy_accepted": False},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_defined_variables_set_properly(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "testComponent",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "testComponent"},
                    "test",
                ]
            },
            actions=[
                {
                    "variable": "userDefinedVar",
                    "action": {
                        "type": "variable",
                        "value": {"+": [{"var": "userDefinedVar"}, 1]},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step,
            data={"testComponent": "test"},
        )
        SubmissionValueVariableFactory.create(
            form_variable__key="userDefinedVar",
            form_variable__source=FormVariableSources.user_defined,
            form_variable__data_type=FormVariableDataTypes.int,
            submission=submission,
            key="userDefinedVar",
            value=0,
        )

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        user_defined_variable = submission.submissionvaluevariable_set.get(
            key="userDefinedVar"
        )

        self.assertEqual(user_defined_variable.value, 1)

    @tag("gh-2096")
    @override_settings(LANGUAGE_CODE="en")
    def test_complete_but_one_step_cant_be_submitted(self):
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "key": "someCondition",
                        "type": "radio",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form_step.form,
            json_logic_trigger={
                "==": [
                    {"var": "someCondition"},
                    "a",
                ]
            },
            actions=[
                {
                    "action": {
                        "type": "disable-next",
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form_step.form)
        SubmissionStepFactory.create(
            submission=submission,
            data={"someCondition": "a"},
            form_step=form_step,
        )

        self._add_submission_to_session(submission)
        response = self.client.post(
            reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
            {"privacy_policy_accepted": True},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.json()

        self.assertEqual(
            data["invalidParams"][0]["reason"],
            "Submission of this form is not allowed due to the answers submitted in a step.",
        )


@temp_private_root()
class SetSubmissionPriceOnCompletionTests(SubmissionsMixin, APITestCase):
    """
    Make assertions about price derivation on submission completion.
    """

    def test_no_product_no_price_rules(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__product=None,
            form__payment_backend="demo",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.steps[0].form_step,
            data={"foo": "bar"},
        )
        with self.subTest(part="check data setup"):
            self.assertFalse(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

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

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertFalse(submission.payment_required)
        self.assertIsNone(submission.price)

    def test_use_product_price(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.steps[0].form_step,
            data={"foo": "bar"},
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("123.45"))

    def test_price_rules_specified(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
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
        FormPriceLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
            price=Decimal("51.15"),
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

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
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
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
        FormPriceLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "test-key"}, "nottest"]},
            price=Decimal("51.15"),
        )
        with self.subTest(part="check data setup"):
            self.assertTrue(submission.payment_required)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("123.45"))
