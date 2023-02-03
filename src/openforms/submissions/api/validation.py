"""
Perform submission-level validation.

TODO: refactor/rework the entire way we _run_ the validations and communicate them back
to the frontend.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from rest_framework import serializers
from rest_framework.request import Request

from openforms.api.utils import mark_experimental
from openforms.forms.constants import SubmissionAllowedChoices

from ..form_logic import check_submission_logic
from ..models import Submission, SubmissionStep
from .fields import NestedSubmissionRelatedField


@dataclass
class InvalidCompletion:
    submission: Submission
    privacy_policy_accepted: bool
    incomplete_steps: List[SubmissionStep] = field(default_factory=list)
    request: Request = None

    def validate(self) -> Optional["CompletionValidationSerializer"]:
        checks = [
            any([self.incomplete_steps]),
            self.submission.form.submission_allowed != SubmissionAllowedChoices.yes,
        ]
        invalid = any(checks)
        if not invalid and self.submission.privacy_policy_accepted:
            return None

        return CompletionValidationSerializer(
            instance=self, context={"request": self.request}
        )


class IncompleteStepSerializer(serializers.Serializer):
    form_step = NestedSubmissionRelatedField(
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid",
        instance_lookup_kwargs={
            "form_uuid_or_slug": "form__uuid",
        },
    )


@mark_experimental
class CompletionValidationSerializer(serializers.Serializer):
    incomplete_steps = IncompleteStepSerializer(many=True)
    submission_allowed = serializers.ChoiceField(
        choices=SubmissionAllowedChoices,
        source="submission.form.submission_allowed",
        read_only=True,
    )
    privacy_policy_accepted = serializers.BooleanField()


def is_step_unexpectedly_incomplete(submission_step: "SubmissionStep") -> bool:
    if not submission_step.completed and submission_step.is_applicable:
        return True
    return False


def validate_submission_completion(
    submission: Submission, request=None
) -> Optional[CompletionValidationSerializer]:
    # check that all required steps are completed
    state = submission.load_execution_state()

    # When loading the state, knowledge of which steps are not applicable is lost
    check_submission_logic(submission)

    incomplete_steps = [
        submission_step
        for submission_step in state.submission_steps
        if is_step_unexpectedly_incomplete(submission_step)
    ]

    completion = InvalidCompletion(
        submission=submission,
        privacy_policy_accepted=submission.privacy_policy_accepted,
        incomplete_steps=incomplete_steps,
        request=request,
    )
    return completion.validate()
