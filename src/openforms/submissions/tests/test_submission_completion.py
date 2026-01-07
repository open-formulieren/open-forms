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

from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.formio.constants import DataSrcOptions
from openforms.forms.constants import StatementCheckboxChoices, SubmissionAllowedChoices
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.registrations.base import BasePlugin
from openforms.registrations.registry import Registry
from openforms.registrations.tests.utils import patch_registry
from openforms.submissions.pricing import InvalidPrice
from openforms.utils.tests.feature_flags import disable_feature_flag
from openforms.variables.constants import FormVariableDataTypes

from ..constants import SUBMISSIONS_SESSION_KEY, PostSubmissionEvents
from ..form_logic import evaluate_form_logic
from ..logic.actions import LogicActionTypes
from ..models import SubmissionStep
from ..tasks import on_post_submission_event
from ..utils import persist_user_defined_variables
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
                    "name": "steps.0.nonFieldErrors",
                    "code": "incomplete",
                    "reason": "Step 'Personal Details' is not yet completed.",
                }
            ],
        )

    def test_component_level_validation(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "firstName",
                        "label": "First name",
                        "validate": {
                            "required": True,
                            "maxLength": 20,
                        },
                    }
                ]
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "firstName": "this value is longer than twenty characters and should not validate"
            },
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_param_names = [
            param["name"] for param in response.json()["invalidParams"]
        ]
        self.assertIn("steps.0.data.firstName", invalid_param_names)

    @patch("openforms.submissions.api.mixins.on_post_submission_event")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission(self, mock_on_post_submission_event):
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
        self.assertIn("statusUrl", response.json())

        # assert that the async celery task execution is scheduled
        mock_on_post_submission_event.assert_called_once_with(
            submission.id, PostSubmissionEvents.on_completion
        )

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

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        self.assertEqual(response_data["code"], "submission-not-allowed")
        self.assertEqual(
            response_data["detail"], "Submission is not enabled for this form."
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_submit_form_with_submission_disabled_without_overview(self):
        submission = SubmissionFactory.create(
            form__submission_allowed=SubmissionAllowedChoices.no_without_overview,
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response_data = response.json()
        self.assertEqual(response_data["code"], "submission-not-allowed")
        self.assertEqual(
            response_data["detail"], "Submission is not enabled for this form."
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

        # assert that identifying attributes are hashed on completion
        submission.refresh_from_db()

        value = submission.auth_info.value
        self.assertTrue(
            bool(submission.auth_info.value),
            "Expected a hashed value instead of empty value",
        )
        self.assertNotEqual(value, "foo")

    def test_privacy_policy_and_statement_of_truth_accepted(self):
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
            "openforms.forms.models.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                ask_privacy_consent=True, ask_statement_of_truth=True
            ),
        ):
            response = self.client.post(
                reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
                data={
                    "privacy_policy_accepted": True,
                    "statement_of_truth_accepted": True,
                },
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        submission.refresh_from_db()

        self.assertTrue(submission.privacy_policy_accepted)
        self.assertTrue(submission.statement_of_truth_accepted)

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
                    "code": "required",
                    "reason": "You must accept the privacy policy.",
                }
            ],
        )

    def test_submission_privacy_policy_not_accepted_not_required_on_form(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__ask_privacy_consent=StatementCheckboxChoices.disabled,
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
        )
        self._add_submission_to_session(submission)

        response = self.client.post(
            reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
            data={"privacy_policy_accepted": False},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
            "openforms.forms.models.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(ask_privacy_consent=False),
        ):
            response = self.client.post(
                reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
                data={"privacy_policy_accepted": False},
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @disable_feature_flag("PERSIST_USER_DEFINED_VARIABLES_UPON_STEP_COMPLETION")
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
            submission=submission,
            key="userDefinedVar",
            value=0,
            data_type=FormVariableDataTypes.int,
            form_variable__user_defined=True,
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
            form_definition__name="Step 1",
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
                    "form_step_uuid": str(form_step.uuid),
                    "action": {"type": "disable-next"},
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

        self.assertEqual(data["invalidParams"][0]["name"], "steps.0.nonFieldErrors")
        self.assertEqual(
            data["invalidParams"][0]["reason"],
            "Step 'Step 1' is blocked.",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_submission_truth_declaration_not_accepted(self):
        form = FormFactory.create(
            submission_confirmation_template="Thank you for submitting {{ foo }}."
        )
        form_step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=form_step, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        with self.subTest("Truth declaration not in body"):
            with patch(
                "openforms.forms.models.form.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(ask_statement_of_truth=True),
            ):
                response = self.client.post(
                    reverse(
                        "api:submission-complete", kwargs={"uuid": submission.uuid}
                    ),
                    data={
                        "privacy_policy_accepted": True,
                    },
                )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json()["invalidParams"],
                [
                    {
                        "name": "statementOfTruthAccepted",
                        "code": "required",
                        "reason": "You must declare the form to be filled out truthfully.",
                    }
                ],
            )

        with self.subTest("Truth declaration in body but not accepted"):
            with patch(
                "openforms.forms.models.form.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(ask_statement_of_truth=True),
            ):
                response = self.client.post(
                    reverse(
                        "api:submission-complete", kwargs={"uuid": submission.uuid}
                    ),
                    data={
                        "privacy_policy_accepted": True,
                        "statement_of_truth_accepted": False,
                    },
                )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json()["invalidParams"],
                [
                    {
                        "name": "statementOfTruthAccepted",
                        "code": "required",
                        "reason": "You must declare the form to be filled out truthfully.",
                    }
                ],
            )

    def test_submission_truth_declaration_not_accepted_but_not_required(self):
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
            "openforms.forms.models.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(ask_statement_of_truth=False),
        ):
            response = self.client.post(
                reverse("api:submission-complete", kwargs={"uuid": submission.uuid}),
                data={
                    "privacy_policy_accepted": True,
                    "statement_of_truth_accepted": False,
                },
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tag("gh-4187")
    def test_dynamic_configuration_evaluated(self):
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "key": "someCondition",
                        "type": "radio",
                        "openForms": {
                            "dataSrc": DataSrcOptions.variable,
                            "itemsExpression": [
                                ["a", "A"],
                            ],
                        },
                    },
                ]
            },
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

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_form_submission_counter_is_incremented(self):
        form = FormFactory.create(submission_limit=1, submission_counter=0)
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        self.client.post(endpoint, {"privacy_policy_accepted": True})

        form.refresh_from_db()

        self.assertEqual(form.submission_counter, 1)

    def test_form_submission_counter_is_not_incremented(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        self.client.post(endpoint, {"privacy_policy_accepted": True})

        form.refresh_from_db()

        self.assertEqual(form.submission_counter, 0)


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
            form__price_logic__price_variable="totalPrice",
            form__price_logic__price_value=9.6,
            form__price_logic__json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
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
            form__price_logic__price_variable="totalPrice",
            form__price_logic__price_value=51.15,
            form__price_logic__json_logic_trigger={"==": [{"var": "test-key"}, "test"]},
        )
        FormVariableFactory.create(
            key="test-key",
            form=submission.form,
            form_definition=submission.form.formstep_set.get().form_definition,
        )

        # Simulate submitting a step. This will evaluate logic and persist the
        # user-defined variables
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"test-key": "test"},
        )
        evaluate_form_logic(submission, submission.submissionstep_set.get())
        persist_user_defined_variables(submission)

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertTrue(submission.payment_required)
        self.assertEqual(submission.price, Decimal("51.15"))

    def test_price_rules_specified_but_no_match(self):
        """
        When there is ambiguity, we bail out instead of guessing/falling back to
        product price.
        """
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__product__price=Decimal("123.45"),
            form__payment_backend="demo",
            form__price_logic__price_variable="totalPrice",
            form__price_logic__price_value=51.15,
            form__price_logic__json_logic_trigger={
                "==": [{"var": "test-key"}, "nottest"]
            },
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
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with self.assertRaises(InvalidPrice):
            self.client.post(endpoint, {"privacy_policy_accepted": True})


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SetRegistrationBackendTests(SubmissionsMixin, APITestCase):
    "Registration backend can be set with a form action"

    def setUp(self):
        super().setUp()
        mock_register = Registry()
        self.mock_calls = mock_calls = []

        @mock_register("mock")
        class MockPlugin(BasePlugin):
            verbose_name = "Mock RegistrationBackend"

            def register_submission(self, *args, **kwargs):
                mock_calls.append((args, kwargs))

        backend_field = FormRegistrationBackendFactory._meta.model._meta.get_field(
            "backend"
        )
        self.monkeypatch = patch_registry(backend_field, mock_register)

    def test_single_backend_needs_no_logic(self):
        submission = SubmissionFactory.from_data({"foo": 1})
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="mock",
            options={"isbn": "0-19-280142-2"},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.monkeypatch:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        self.assertEqual(len(self.mock_calls), 1)
        submission_in_args = self.mock_calls[0][0][0]
        self.assertEqual(
            submission_in_args.registration_backend.options["isbn"], "0-19-280142-2"
        )

    def test_multi_backend_no_logic(self):
        submission = SubmissionFactory.from_data({"foo": 1})
        FormRegistrationBackendFactory.create(
            form=submission.form,
            key="M",
            name="Mockingbird",
            backend="mock",
            options={"isbn": "0-19-280142-2"},
        )
        FormRegistrationBackendFactory.create(
            form=submission.form,
            key="BM",
            name="Double Mockingbird",
            backend="mock",
            options={"url": "https://www.angelfire.com/tx4/cus/combinator/birds.html"},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.monkeypatch:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        # it uses the first
        self.assertEqual(len(self.mock_calls), 1)
        submission_in_args = self.mock_calls[0][0][0]
        self.assertEqual(
            submission_in_args.registration_backend.options["isbn"], "0-19-280142-2"
        )
        # and logs debug data to the timeline
        logged_events = TimelineLogProxy.objects.filter_event("registration_debug")
        self.assertTrue(
            next(
                (
                    log
                    for log in logged_events
                    if log.extra_data["backend"] == {"key": "M", "name": "Mockingbird"}
                ),
                False,
            )
        )

    def test_setting_backend_with_logic(self):
        submission = SubmissionFactory.from_data({"foo": 1})
        FormRegistrationBackendFactory.create(
            form=submission.form,
            backend="mock",
            options={"isbn": "0-19-280142-2"},
        )
        FormRegistrationBackendFactory.create(
            form=submission.form,
            key="to_pick",
            backend="mock",
            options={"url": "https://www.angelfire.com/tx4/cus/combinator/birds.html"},
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "foo"}, 1]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "to_pick",
                    },
                }
            ],
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.monkeypatch:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        self.assertEqual(len(self.mock_calls), 1)
        submission_in_args = self.mock_calls[0][0][0]
        self.assertEqual(
            submission_in_args.registration_backend.options["url"],
            "https://www.angelfire.com/tx4/cus/combinator/birds.html",
        )

    def test_setting_faulty_backend_with_logic(self):
        submission = SubmissionFactory.from_data({"foo": 1})
        FormRegistrationBackendFactory.create(
            form=submission.form,
            key="M",
            backend="mock",
        )
        FormRegistrationBackendFactory.create(
            form=submission.form,
            key="BM",
            backend="mock",
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "foo"}, 1]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "not M",
                    },
                }
            ],
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.monkeypatch:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        # Still tries to use default
        self.assertEqual(len(self.mock_calls), 1)
        submission_in_args = self.mock_calls[0][0][0]
        self.assertEqual(submission_in_args.registration_backend.key, "M")
        # but logs the fact
        logged_events = TimelineLogProxy.objects.filter_event("registration_debug")
        self.assertTrue(
            next(
                (
                    log
                    for log in logged_events
                    if log.extra_data.get("error", "")
                    == "FormRegistrationBackend matching query does not exist."
                    and log.extra_data["backend"]["key"] == "not M"
                ),
                False,
            )
        )
