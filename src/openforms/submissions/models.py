import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models


class Submission(models.Model):
    """
    Container for submission steps that hold the actual submitted data.
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    form = models.ForeignKey('core.Form', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    backend_result = JSONField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'

    def __str__(self):
        return f'Submission {self.pk}: Form {self.form_id} submitted on {self.created_on}'

    @property
    def is_completed(self):
        return bool(self.completed_on)


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    form_step = models.ForeignKey('core.FormStep', on_delete=models.CASCADE)
    data = JSONField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'SubmissionStep'
        verbose_name_plural = 'SubmissionSteps'

    def __str__(self):
        return f'SubmissionStep {self.pk}: Submission {self.submission_id} submitted on {self.created_on}'
