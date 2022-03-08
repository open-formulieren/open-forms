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
    incomplete_steps: List[SubmissionStep] = field(default_factory=list)
    invalid_prefilled_fields: List[str] = field(default_factory=list)
    request: Request = None

    def validate(self) -> Optional["CompletionValidationSerializer"]:
        checks = [
            any([self.incomplete_steps]),
            any(self.invalid_prefilled_fields),
            self.submission.form.submission_allowed != SubmissionAllowedChoices.yes,
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


@mark_experimental
class CompletionValidationSerializer(serializers.Serializer):
    incomplete_steps = IncompleteStepSerializer(many=True)
    submission_allowed = serializers.ChoiceField(
        choices=SubmissionAllowedChoices,
        source="submission.form.submission_allowed",
        read_only=True,
    )
    invalid_prefilled_fields = serializers.ListField(child=serializers.CharField())


def validate_submission_completion(
    submission: Submission, request=None
) -> Optional[CompletionValidationSerializer]:
    # check that all required steps are completed
    state = submission.load_execution_state()

    # When loading the state, knowledge of which steps are not applicable is lost
    check_submission_logic(submission)

    incomplete_steps = []
    invalid_prefilled_fields = []
    for submission_step in state.submission_steps:
        invalid_prefilled_fields += get_invalid_prefilled_fields(
            submission_step, submission
        )
        if submission_step.form_step.optional:
            continue
        if not submission_step.completed and submission_step.is_applicable:
            incomplete_steps.append(submission_step)

    completion = InvalidCompletion(
        submission=submission,
        incomplete_steps=incomplete_steps,
        invalid_prefilled_fields=invalid_prefilled_fields,
        request=request,
    )
    return completion.validate()


def get_invalid_prefilled_fields(
    submission_step: "SubmissionStep", submission: "Submission"
) -> List[str]:
    invalid_prefilled_fields = []

    for component in submission_step.form_step.iter_components():
        if "prefill" not in component or component["prefill"]["plugin"] == "":
            continue

        if not component["disabled"]:
            continue

        plugin_name = component["prefill"]["plugin"]
        attribute_name = component["prefill"]["attribute"]
        if (
            submission_step.data[component["key"]]
            != submission.prefill_data[plugin_name][attribute_name]
        ):
            invalid_prefilled_fields.append(component["label"])

    return invalid_prefilled_fields
