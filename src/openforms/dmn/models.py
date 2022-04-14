from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission


class DMNEvaluationResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    component = models.CharField(_("DMN component key"), max_length=255)
    result = models.JSONField(_("result"), default=dict, blank=True, null=True)

    class Meta:
        unique_together = ("submission", "component")
