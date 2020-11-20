import uuid
from typing import Optional

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
