from django.contrib.postgres.fields import JSONField
from django.db import models


class FormSubmission(models.Model):
    """
    Form Submission Data model to hold form submission json data.
    """
    form = models.ForeignKey('core.Form', on_delete=models.CASCADE)
    submitted_on = models.DateTimeField(auto_now_add=True)
    data = JSONField()

    def __str__(self):
        return f'Submission - {self.form} - {self.submitted_on}'

    class Meta:
        verbose_name = 'Form Submission'
        verbose_name_plural = 'Form Submissions'
