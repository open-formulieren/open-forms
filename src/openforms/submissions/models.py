from django.contrib.postgres.fields import JSONField
from django.db import models


class Submission(models.Model):
    """
    Submission data model to hold form submission JSON data.
    """
    form = models.ForeignKey('core.Form', blank=True, null=True, on_delete=models.SET_NULL)
    form_name = models.CharField(max_length=50)
    submitted_on = models.DateTimeField(auto_now_add=True)
    data = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'

    def __str__(self):
        return f'Submission {self.pk}: Form {self.form_name} ({self.form_pk}) submitted on {self.submitted_on}'

    def save(self, *args, **kwargs):
        if self.form:
            self.form_name = self.form.name

        super().save(*args, **kwargs)