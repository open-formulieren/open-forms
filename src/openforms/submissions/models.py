import uuid
from typing import List, Optional

from django.contrib.postgres.fields import JSONField
from django.db import models

from openforms.core.models import FormStep
from openforms.utils.fields import StringUUIDField
from openforms.utils.validators import validate_bsn


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """

    uuid = StringUUIDField(unique=True, default=uuid.uuid4)
    form = models.ForeignKey("core.Form", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    backend_result = JSONField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)
    bsn = models.CharField(
        max_length=9, default="", blank=True, validators=(validate_bsn,)
    )
    current_step = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

    def __str__(self):
        return f"Submission {self.pk}: Form {self.form_id} started on {self.created_on}"

    @property
    def is_completed(self):
        return bool(self.completed_on)

    @property
    def steps(self) -> List["SubmissionStep"]:
        # fetch the existing DB records for submitted form steps
        _submission_steps = self.submissionstep_set.select_related(
            "form_step", "form_step__form_definition"
        )
        submission_steps = {step.form_step: step for step in _submission_steps}
        form_steps = self.form.formstep_set.select_related("form_definition").order_by(
            "order"
        )

        # build the resulting list - some SubmissionStep instances will probably not exist
        # in the database yet - this is on purpose!
        steps: List[SubmissionStep] = []

        for form_step in form_steps:
            if form_step in submission_steps:
                steps.append(submission_steps[form_step])
            else:
                # there's no known DB record for this, so we create a fresh, unsaved
                # instance and return this
                new_step = SubmissionStep(
                    # nothing assigned yet, and on next call it'll be a different value
                    # if we rely on the default
                    uuid=None,
                    submission=self,
                    form_step=form_step,
                )
                steps.append(new_step)

        return steps

    def get_next_step(self) -> Optional[FormStep]:
        """
        Determine which is the next step for the current submission.

        TODO: look at the state of completed steps and figure it out from there.
        """
        form_steps = self.form.formstep_set.all()
        return form_steps.first()


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    form_step = models.ForeignKey("core.FormStep", on_delete=models.CASCADE)
    data = JSONField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SubmissionStep"
        verbose_name_plural = "SubmissionSteps"
        unique_together = (("submission", "form_step"),)

    def __str__(self):
        return f"SubmissionStep {self.pk}: Submission {self.submission_id} submitted on {self.created_on}"

    @property
    def available(self) -> bool:
        return True

    @property
    def completed(self) -> bool:
        # TODO: should check that all the data for the form definition is present?
        # and validates?
        # For now - if it's been saved, we assume that was because it was completed
        return bool(self.pk and self.data is not None)

    @property
    def current(self) -> bool:
        # TODO: implement logic
        return True

    @property
    def optional(self) -> bool:
        # TODO: implement logic
        return False
