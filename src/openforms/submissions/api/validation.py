"""
Perform submission-level validation.

TODO: refactor/rework the entire way we _run_ the validations and communicate them back
to the frontend.
"""

from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.utils import mark_experimental
from openforms.formio.service import build_serializer

from ..form_logic import check_submission_logic
from ..models import Submission, SubmissionStep
from .fields import (
    PrivacyPolicyAcceptedField,
    SubmissionAllowedField,
    TruthDeclarationAcceptedField,
)


@mark_experimental
class CompletionValidationSerializer(serializers.Serializer):
    incomplete_steps = serializers.ListField(
        child=serializers.CharField(),
        validators=[
            MaxLengthValidator(
                limit_value=0,
                message=_("Not all applicable steps have been completed: %(value)s"),
            )
        ],
    )
    submission_allowed = SubmissionAllowedField()
    privacy_policy_accepted = PrivacyPolicyAcceptedField()
    statement_of_truth_accepted = TruthDeclarationAcceptedField()
    contains_blocked_steps = serializers.BooleanField()

    def validate_contains_blocked_steps(self, value):
        if value:
            raise serializers.ValidationError(
                _(
                    "Submission of this form is not allowed due to the answers submitted in a step."
                )
            )

    def validate(self, attrs: dict):
        submission: Submission = self.context["submission"]

        formio_validation_errors = []

        data = submission.data
        for step in submission.steps:
            errors = {}
            assert step.form_step
            components = step.form_step.form_definition.configuration["components"]

            step_data_serializer = build_serializer(components, data=data)
            if not step_data_serializer.is_valid():
                errors = step_data_serializer.errors

            if errors:
                formio_validation_errors.append({"data": errors})
            else:
                formio_validation_errors.append(None)

        if any(formio_validation_errors):
            raise serializers.ValidationError({"steps": formio_validation_errors})

        return attrs

    def save(self, **kwargs):
        submission = self.context["submission"]
        submission.privacy_policy_accepted = True
        submission.statement_of_truth_accepted = True
        submission.save()


def is_step_unexpectedly_incomplete(submission_step: "SubmissionStep") -> bool:
    if not submission_step.completed and submission_step.is_applicable:
        return True
    return False


def get_submission_completion_serializer(
    submission: Submission, request
) -> CompletionValidationSerializer:
    # check that all required steps are completed
    state = submission.load_execution_state()

    # When loading the state, knowledge of which steps are not applicable is lost
    check_submission_logic(submission)

    incomplete_steps = [
        submission_step.form_step.form_definition.name
        for submission_step in state.submission_steps
        if is_step_unexpectedly_incomplete(submission_step)
    ]

    return CompletionValidationSerializer(
        data={
            "incomplete_steps": incomplete_steps,
            "submission_allowed": submission.form.submission_allowed,
            "privacy_policy_accepted": request.data.get("privacy_policy_accepted"),
            "statement_of_truth_accepted": request.data.get(
                "statement_of_truth_accepted", False
            ),
            "contains_blocked_steps": any(
                not submission_step.can_submit
                for submission_step in state.submission_steps
            ),
        },
        context={"request": request, "submission": submission},
    )
