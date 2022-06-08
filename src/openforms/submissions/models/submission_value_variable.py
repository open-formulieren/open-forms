from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from glom import Assign, PathAccessError, glom

from openforms.forms.models.form_variable import FormVariable

from ..constants import SubmissionValueVariableSources
from .submission import Submission

if TYPE_CHECKING:
    from .submission_step import SubmissionStep


@dataclass
class SubmissionValueVariablesState:
    variables: Dict[str, "SubmissionValueVariable"]

    def get_variable(self, key: str) -> Optional["SubmissionValueVariable"]:
        return self.variables[key]

    def get_data(self, submission_step: Optional["SubmissionStep"] = None) -> dict:
        submission_variables = self.variables
        if submission_step:
            submission_variables = self.get_variables_in_submission_step(
                submission_step
            )

        data = {}
        for variable_key, variable in submission_variables.items():
            if (
                variable.value != ""
                or variable.source
                == SubmissionValueVariableSources.sensitive_data_cleaner
            ):
                glom(data, Assign(variable_key, variable.value, missing=dict))
        return data

    def get_variables_in_submission_step(
        self, submission_step: "SubmissionStep"
    ) -> Dict[str, "SubmissionValueVariable"]:
        form_definition = submission_step.form_step.form_definition
        return {
            variable_key: variable
            for variable_key, variable in self.variables.items()
            if variable.form_variable.form_definition == form_definition
        }

    @classmethod
    def get_state(cls, submission: "Submission") -> "SubmissionValueVariablesState":
        # Get the SubmissionValueVariables already saved in the database
        saved_submission_value_variables = (
            submission.submissionvaluevariable_set.all().select_related(
                "form_variable__form_definition"
            )
        )

        # Get all the form variables for the SubmissionVariables that have not been created yet
        form_variables = FormVariable.objects.filter(
            ~Q(
                id__in=saved_submission_value_variables.values_list(
                    "form_variable__id", flat=True
                )
            ),
            form=submission.form,
        ).select_related("form_definition")

        unsaved_value_variables = {}
        for form_variable in form_variables:
            # TODO Fill source field
            key = form_variable.key
            unsaved_submission_var = SubmissionValueVariable(
                submission=submission,
                form_variable=form_variable,
                key=key,
                value=form_variable.get_initial_value(),
            )
            unsaved_value_variables[key] = unsaved_submission_var

        return cls(
            variables={
                **{
                    variable.key: variable
                    for variable in saved_submission_value_variables
                },
                **unsaved_value_variables,
            }
        )


class SubmissionValueVariableManager(models.Manager):
    def bulk_create_or_update(
        self, submission_step, data, update_missing_variables: bool = False
    ):
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
        for key, variable in submission_step_variables.items():
            try:
                variable.value = glom(data, key)
            except PathAccessError:
                if update_missing_variables:
                    variable.value = variable.form_variable.get_initial_value()

            if not variable.pk:
                variables_to_create.append(variable)
            else:
                variables_to_update.append(variable)

        self.bulk_create(variables_to_create)
        self.bulk_update(variables_to_update, fields=["value"])


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
        null=True,
        blank=True,
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
        auto_now_add=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("modified at"),
        help_text=_("The date/time at which the value of this variable was last set"),
        null=True,
        blank=True,
        auto_now=True,
    )

    objects = SubmissionValueVariableManager()

    class Meta:
        verbose_name = _("Submission value variable")
        verbose_name_plural = _("Submission values variables")
        unique_together = [["submission", "key"], ["submission", "form_variable"]]

    def __str__(self):
        if self.form_variable:
            return _("Submission value variable {name}").format(
                name=self.form_variable.name
            )
        return _("Submission value variable {key}").format(key=self.key)
