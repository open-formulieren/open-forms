"""
Perform submission-level validation.

TODO: refactor/rework the entire way we _run_ the validations and communicate them back
to the frontend.
"""
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.utils import mark_experimental
from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import SubmissionAllowedChoices

from ..form_logic import check_submission_logic
from ..models import Submission, SubmissionStep


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
    submission_allowed = serializers.ChoiceField(
        choices=SubmissionAllowedChoices.choices,
    )
    privacy_policy_accepted = serializers.BooleanField()

    def validate_privacy_policy_accepted(self, privacy_policy_accepted: bool) -> None:
        config = GlobalConfiguration.get_solo()
        privacy_policy_valid = (
            privacy_policy_accepted if config.ask_privacy_consent else True
        )
        if not privacy_policy_valid:
            raise serializers.ValidationError(
                _("Privacy policy must be accepted before completing submission.")
            )

    def validate_submission_allowed(self, submission_allowed):
        if submission_allowed != SubmissionAllowedChoices.yes:
            raise serializers.ValidationError(
                _("Submission of this form is not allowed.")
            )

    def save(self, **kwargs):
        submission = self.context["submission"]
        submission.privacy_policy_accepted = True
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
        },
        context={"request": request, "submission": submission},
    )
