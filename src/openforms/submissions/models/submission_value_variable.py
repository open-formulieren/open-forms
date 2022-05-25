from dataclasses import dataclass
from typing import List

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.forms.models.form_variable import FormVariable

from ..constants import SubmissionValueVariableSources
from .submission import Submission


@dataclass
class SubmissionValueVariablesState:
    variables: List["SubmissionValueVariable"]

    def get_variables_to_prefill(self):
        return [
            variable
            for variable in self.variables
            if variable.source == SubmissionValueVariableSources.prefill
        ]

    def get_data(self):
        return {variable.key: variable.value for variable in self.variables}

    def get_variables_in_submission_step(self, submission_step):
        form_variables = FormVariable.objects.filter(
            form_definition=submission_step.form_step.form_definition
        )

        return [
            variable
            for variable in self.variables
            if variable.form_variable in form_variables
        ]


class SubmissionValueVariable(models.Model):
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
    # Added for the case where a FormVariable has been deleted, but there is still a SubmissionValueValue.
    # Having a key will help debug where the SubmissionValueValue came from
    key = models.SlugField(
        verbose_name=_("key"),
        help_text=_("Key of the variable"),
        max_length=100,
    )
    value = models.JSONField(
        verbose_name=_("value"),
        help_text=_("The value of the variable"),
    )
    source = models.CharField(
        verbose_name=_("source"),
        help_text=_("Where variable value came from"),
        choices=SubmissionValueVariableSources.choices,
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
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Submission value variable")
        verbose_name_plural = _("Submission values variables")

    def __str__(self):
        if self.form_variable:
            return _("Submission value variable %(name)s") % {
                "name": self.form_variable.name
            }
        return _("Submission value variable %(key)s") % {"key": self.key}

    @classmethod
    def bulk_create_or_update(cls, submission_step, data):
        submission = submission_step.submission

        submission_value_variables_state = (
            submission.load_submission_value_variables_state()
        )
        submission_step_variables = (
            submission_value_variables_state.get_variables_in_submission_step(
                submission_step
            )
        )

        variables_to_create = []
        variables_to_update = []
        for variable in submission_step_variables:
            key = variable.key
            if key in data:
                variable.value = data[key]
            else:
                variable.value = ""

            if not variable.pk:
                variables_to_create.append(variable)
            else:
                variable.modified_at = timezone.now()
                variables_to_update.append(variable)

        cls.objects.bulk_create(variables_to_create)
        cls.objects.bulk_update(variables_to_update, fields=["value", "modified_at"])
