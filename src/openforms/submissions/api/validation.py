from dataclasses import dataclass, field
from typing import List

from rest_framework import serializers
from rest_framework.request import Request

from ..form_logic import evaluate_form_logic
from ..models import Submission, SubmissionStep
from .fields import NestedSubmissionRelatedField


@dataclass
class InvalidCompletion:
    submission: Submission
    incomplete_steps: List[SubmissionStep] = field(default_factory=list)
    request: Request = None

    def is_valid(self, raise_exception=False):
        invalid = any([self.incomplete_steps])
        if not raise_exception:
            return not invalid

        if invalid:
            serializer = CompletionValidationSerializer(
                instance=self, context={"request": self.request}
            )
            raise serializers.ValidationError(serializer.data)


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


def validate_submission_completion(submission: Submission, request=None):
    # check that all required steps are completed
    state = submission.load_execution_state()

    # When loading the state, knowledge of which steps are not applicable is lost
    for submission_step in submission.steps:
        evaluate_form_logic(submission, submission_step, submission_step.data)

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
    completion.is_valid(raise_exception=True)
