"""
Perform submission-level validation.
"""

from typing import TYPE_CHECKING, TypedDict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework.request import Request
from rest_framework.settings import api_settings

from openforms.formio.service import build_serializer, get_dynamic_configuration
from openforms.forms.models import FormDefinition, FormStep

from ..models import Submission, SubmissionStep
from .fields import PrivacyPolicyAcceptedField, TruthDeclarationAcceptedField

NON_FIELD_ERRORS_KEY = api_settings.NON_FIELD_ERRORS_KEY


def is_step_unexpectedly_incomplete(submission_step: SubmissionStep) -> bool:
    if not submission_step.completed and submission_step.is_applicable:
        return True
    return False


class SubmissionCompletionSerializerContext(TypedDict):
    request: Request
    submission: Submission


type StepValidationErrors = dict[str, ErrorDetail] | dict[str, StepValidationErrors]


class SubmissionCompletionSerializer(serializers.Serializer):
    """
    Validate the submission completion.

    The input validation requires the statement checkboxes to be provided before
    completion can be considered. If that is fine, we run validation on the state of
    the submission, which is a bit "weird" in the sense that we're double-checking
    earlier user-input and not directly validating ``request.data`` items.

    If all is well, we return the status URL to check the background processing,
    otherwise the validation errors are raised for the frontend to handle.
    """

    _context: SubmissionCompletionSerializerContext  # pyright: ignore[reportIncompatibleVariableOverride]
    if TYPE_CHECKING:

        @property
        def context(  # pyright: ignore[reportIncompatibleMethodOverride]
            self,
        ) -> SubmissionCompletionSerializerContext: ...

    # statement checkboxes on the overview page
    privacy_policy_accepted = PrivacyPolicyAcceptedField(required=False)
    statement_of_truth_accepted = TruthDeclarationAcceptedField(required=False)

    status_url = serializers.URLField(
        label=_("status check endpoint"),
        help_text=_(
            "The API endpoint where the background processing status can be checked. "
            "After calling the completion endpoint, this status URL should be polled "
            "to report the processing status back to the end-user. Note that the "
            "endpoint contains a token which invalidates on state changes and after "
            "one day."
        ),
        read_only=True,
    )

    def validate(self, attrs):
        submission = self.context["submission"]

        # run the state validation for the submission as a whole, not depending on any
        # particular user input from the request data. We build up an array of errors
        # for a given step - if there are no issues, an empty dict is used as the index
        # of errors must match the index of the steps in the form.
        all_step_errors: list[StepValidationErrors] = []
        step_errors: StepValidationErrors

        data = submission.data

        for step in submission.steps:
            form_step = step.form_step
            assert isinstance(form_step, FormStep)
            form_definition = form_step.form_definition
            assert isinstance(form_definition, FormDefinition)
            step_name: str = form_definition.name

            step_errors = {}  # we must add *something* to the array

            # check for blocked steps
            if not step.can_submit:
                step_errors = {
                    NON_FIELD_ERRORS_KEY: ErrorDetail(
                        _("Step '{name}' is blocked.").format(name=step_name),
                        code="blocked",
                    )
                }
            # check if the step was skipped somehow
            elif is_step_unexpectedly_incomplete(step):
                step_errors = {
                    NON_FIELD_ERRORS_KEY: ErrorDetail(
                        _("Step '{name}' is not yet completed.").format(name=step_name),
                        code="incomplete",
                    )
                }

            # run the full Formio validation for the step
            if step.is_applicable:
                # evaluate dynamic configuration. We avoid calling `evaluate_form_logic`
                # on purpose to avoid duplicate logic evaluation
                configuration = get_dynamic_configuration(
                    form_definition.configuration_wrapper,
                    self.context["request"],
                    submission=submission,
                    data=data,
                ).configuration
                step_data_serializer = build_serializer(
                    configuration["components"],
                    data=data,
                    context={"submission": submission},
                )
                if not step_data_serializer.is_valid():
                    step_errors["data"] = (  # pyright: ignore[reportArgumentType]
                        step_data_serializer.errors
                    )

            all_step_errors.append(step_errors)

        assert len(all_step_errors) == len(
            submission.steps
        ), "Detected a mismatch in validation errors list with actual submission steps."

        # as soon as one step has problems, we must raise a validation error
        if any(all_step_errors):
            raise serializers.ValidationError({"steps": all_step_errors})

        return attrs

    def save(self, **kwargs) -> None:
        status_url: str = kwargs.pop("status_url")
        submission = self.context["submission"]
        data = self.validated_data

        # persist which checkboxes were accepted
        submission.privacy_policy_accepted = data.get("privacy_policy_accepted", False)
        submission.statement_of_truth_accepted = data.get(
            "statement_of_truth_accepted", False
        )
        submission.save(
            update_fields=[
                "privacy_policy_accepted",
                "statement_of_truth_accepted",
            ]
        )

        # patch up the validated data so that we can emit the status URL
        data["status_url"] = status_url
