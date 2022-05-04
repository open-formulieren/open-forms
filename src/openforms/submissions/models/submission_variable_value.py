from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.forms.models.form_variable import FormVariable

from ..constants import SubmissionVariableValueSources
from .submission import Submission


class SubmissionVariableValue(models.Model):
    submission = models.ForeignKey(
        to=Submission,
        verbose_name=_("submission"),
        help_text=_("The submission to which this variable value is related"),
        on_delete=models.CASCADE,
    )
    form_variable = models.ForeignKey(
        to=FormVariable,
        verbose_name=_("form variable"),
        help_text=_("The form variable to which this value is related"),
        on_delete=models.SET_NULL,  # In case form definitions are edited after a user has filled in a form.
        null=True,
    )
    value = models.JSONField(
        verbose_name=_("value"),
        help_text=_("The value of the variable"),
    )
    source = models.CharField(
        verbose_name=_("source"),
        help_text=_("Where variable value came from"),
        choices=SubmissionVariableValueSources.choices,
        max_length=50,
    )
    language = models.CharField(
        verbose_name=_("language"),
        help_text=_("If this value contains text, in which language is it?"),
        max_length=50,
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_("created at"),
        help_text=_("The date/time at which the value of this variable was created"),
        auto_now=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("modified at"),
        help_text=_("The date/time at which the value of this variable was last set"),
    )
