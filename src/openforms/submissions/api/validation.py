"""
Perform submission-level validation.

TODO: refactor/rework the entire way we _run_ the validations and communicate them back
to the frontend.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from rest_framework import serializers
from rest_framework.request import Request

from openforms.forms.constants import CanSubmitChoices

from ..form_logic import check_submission_logic
from ..models import Submission, SubmissionStep
from .fields import NestedSubmissionRelatedField


@dataclass
class InvalidCompletion:
    submission: Submission
    incomplete_steps: List[SubmissionStep] = field(default_factory=list)
    request: Request = None

    def validate(self) -> Optional["CompletionValidationSerializer"]:
        checks = [
            any([self.incomplete_steps]),
            self.submission.form.can_submit != CanSubmitChoices.yes,
        ]
        invalid = any(checks)
        if not invalid:
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


class CompletionValidationSerializer(serializers.Serializer):
    incomplete_steps = IncompleteStepSerializer(many=True)
    can_submit = serializers.ChoiceField(
        choices=CanSubmitChoices,
        source="submission.form.can_submit",
        read_only=True,
    )


def validate_submission_completion(
    submission: Submission, request=None
) -> Optional[CompletionValidationSerializer]:
    # check that all required steps are completed
    state = submission.load_execution_state()

    # When loading the state, knowledge of which steps are not applicable is lost
    check_submission_logic(submission)

    incomplete_steps = []
    for submission_step in state.submission_steps:
        if submission_step.form_step.optional:
            continue
        if not submission_step.completed and submission_step.is_applicable:
            incomplete_steps.append(submission_step)

    completion = InvalidCompletion(
        submission=submission,
        incomplete_steps=incomplete_steps,
        request=request,
    )
    return completion.validate()
