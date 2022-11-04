from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from django.db import models
from django.utils.translation import gettext_lazy as _

from glom import Assign, PathAccessError, glom

from openforms.forms.models.form_variable import FormVariable
from openforms.variables.service import get_static_variables
from openforms.variables.utils import variable_value_to_python

from ..constants import SubmissionValueVariableSources
from .submission import Submission

if TYPE_CHECKING:  # pragma: nocover
    from .submission_step import SubmissionStep


@dataclass
class SubmissionValueVariablesState:
    submission: "Submission"
    _variables: Optional[Dict[str, "SubmissionValueVariable"]] = field(
        init=False, default=None
    )
    _static_variables: Optional[Dict[str, Any]] = field(init=False, default=None)

    @property
    def variables(self) -> Dict[str, "SubmissionValueVariable"]:
        if not self._variables:
            self._variables = self.collect_variables()
        return self._variables

    @property
    def saved_variables(self) -> Dict[str, "SubmissionValueVariable"]:
        return {
            variable_key: variable
            for variable_key, variable in self.variables.items()
            if variable.pk
        }

    def get_variable(self, key: str) -> "SubmissionValueVariable":
        return self.variables[key]

    def get_data(
        self,
        submission_step: Optional["SubmissionStep"] = None,
        return_unchanged_data: bool = True,
    ) -> dict:
        submission_variables = self.saved_variables
        if submission_step:
            submission_variables = self.get_variables_in_submission_step(
                submission_step, include_unsaved=False
            )

        data = {}
        for variable_key, variable in submission_variables.items():
            if (
                variable.value is None
                and variable.form_variable
                and variable.value == variable.form_variable.initial_value
                and not return_unchanged_data
            ):
                continue

            if variable.source != SubmissionValueVariableSources.sensitive_data_cleaner:
                glom(data, Assign(variable_key, variable.value, missing=dict))
        return data

    def get_variables_in_submission_step(
        self,
        submission_step: "SubmissionStep",
        include_unsaved=True,
    ) -> Dict[str, "SubmissionValueVariable"]:
        configuration_wrapper = (
            submission_step.form_step.form_definition.configuration_wrapper
        )
        keys_in_step = list(configuration_wrapper.component_map.keys())

        variables = self.variables
        if not include_unsaved:
            variables = self.saved_variables

        return {
            variable_key: variable
            for variable_key, variable in variables.items()
            if variable.key in keys_in_step
        }

    def collect_variables(self) -> Dict[str, "SubmissionValueVariable"]:
        # leverage the (already populated) submission state to get access to form
        # steps and form definitions
        submission_state = self.submission.load_execution_state()
        form_definition_map = {
            form_step.form_definition.id: form_step.form_definition
            for form_step in submission_state.form_steps
        }

        # Build a collection of all form variables
        all_form_variables = {
            form_variable.key: form_variable
            for form_variable in self.submission.form.formvariable_set.all()
        }
        # optimize the access from form_variable.form_definition using the already
        # existing map, saving a `select_related` call on data we (probably) already
        # have
        for form_variable in all_form_variables.values():
            if not (form_def_id := form_variable.form_definition_id):
                continue
            form_variable.form_definition = form_definition_map[form_def_id]

        # now retrieve the persisted variables from the submission - avoiding select_related
        # calls since we already have the relevant data
        all_submission_variables = {
            submission_value_variables.key: submission_value_variables
            for submission_value_variables in self.submission.submissionvaluevariable_set.all()
        }
        # do the join by `key`, which is unique across the form
        for variable_key, submission_value_variable in all_submission_variables.items():
            if variable_key not in all_form_variables:
                continue
            submission_value_variable.form_variable = all_form_variables[variable_key]

        # finally, add in the unsaved variables from defualt values
        for variable_key, form_variable in all_form_variables.items():
            # if the key exists from the saved values in the DB, do nothing
            if variable_key in all_submission_variables:
                continue
            # TODO Fill source field
            unsaved_submission_var = SubmissionValueVariable(
                submission=self.submission,
                form_variable=form_variable,
                key=variable_key,
                value=form_variable.get_initial_value(),
                is_initially_prefilled=(form_variable.prefill_plugin != ""),
            )
            all_submission_variables[variable_key] = unsaved_submission_var

        return all_submission_variables

    def remove_variables(self, keys: list) -> None:
        for key in keys:
            if key in self._variables:
                del self._variables[key]

    @property
    def static_variables(self) -> dict:
        if self._static_variables is None:
            self._static_variables = {
                variable.key: variable
                for variable in get_static_variables(submission=self.submission)
            }
        return self._static_variables

    def get_prefill_variables(self) -> List["SubmissionValueVariable"]:
        prefill_vars = []
        for variable in self.variables.values():
            if not variable.is_initially_prefilled:
                continue
            prefill_vars.append(variable)
        return prefill_vars

    def save_prefill_data(self, data: Dict[str, Any]) -> None:
        variables_to_prefill = self.get_prefill_variables()
        for variable in variables_to_prefill:
            if variable.key not in data:
                continue

            variable.value = data[variable.key]
            variable.source = SubmissionValueVariableSources.prefill

        SubmissionValueVariable.objects.bulk_create(variables_to_prefill)

    def set_values(self, data: Dict[str, Any]) -> None:
        """
        Apply the values from ``data`` to the current state of the variables.

        This does NOT persist the values, it only mutates the value instances in place.
        The ``data`` structure maps variable key and (new) values to set on the
        variables in the state.

        :arg data: mapping of variable key to value.

        .. todo:: apply variable.datatype/format to obtain python objects? This also
           needs to properly serialize back to JSON though!
        """
        for key, variable in self.variables.items():
            try:
                new_value = glom(data, key)
            except PathAccessError:
                continue
            variable.value = new_value


class SubmissionValueVariableManager(models.Manager):
    def bulk_create_or_update_from_data(
        self,
        data: dict,
        submission: "Submission",
        submission_step: "SubmissionStep" = None,
        update_missing_variables: bool = False,
    ) -> None:

        submission_value_variables_state = (
            submission.load_submission_value_variables_state()
        )
        submission_variables = submission_value_variables_state.variables
        if submission_step:
            submission_variables = (
                submission_value_variables_state.get_variables_in_submission_step(
                    submission_step
                )
            )

        variables_to_create = []
        variables_to_update = []
        variables_keys_to_delete = []
        for key, variable in submission_variables.items():
            try:
                variable.value = glom(data, key)
            except PathAccessError:
                if update_missing_variables:
                    if variable.pk:
                        variables_keys_to_delete.append(variable.key)
                    else:
                        variable.value = variable.form_variable.get_initial_value()
                    continue

            if not variable.pk:
                variables_to_create.append(variable)
            else:
                variables_to_update.append(variable)

        self.bulk_create(variables_to_create)
        self.bulk_update(variables_to_update, fields=["value"])
        self.filter(submission=submission, key__in=variables_keys_to_delete).delete()

        # Variables that are deleted are not automatically updated in the state
        # (i.e. they remain present with their pk)
        if variables_keys_to_delete:
            submission_value_variables_state.remove_variables(
                keys=variables_keys_to_delete
            )


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
    key = models.TextField(
        verbose_name=_("key"),
        help_text=_("Key of the variable"),
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
    is_initially_prefilled = models.BooleanField(
        verbose_name=_("is initially prefilled"),
        help_text=_("Can this variable be prefilled at the beginning of a submission?"),
        default=False,
        null=True,
        blank=True,
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

    def to_python(self) -> Any:
        """
        Deserialize the value into the appropriate python type.
        """
        # can't see any type information...
        if not self.form_variable_id:
            return self.value

        return variable_value_to_python(self.value, self.form_variable.data_type)
