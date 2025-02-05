from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any, Literal, overload

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.functional import empty
from django.utils.translation import gettext_lazy as _

from openforms.formio.service import FormioData
from openforms.forms.models.form_variable import FormVariable
from openforms.typing import DataMapping, JSONEncodable, JSONObject, JSONSerializable
from openforms.utils.date import format_date_value, parse_datetime, parse_time
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.service import VariablesRegistry, get_static_variables

from ..constants import SubmissionValueVariableSources
from .submission import Submission

if TYPE_CHECKING:
    from .submission_step import SubmissionStep


logger = logging.getLogger(__name__)


class ValueEncoder(DjangoJSONEncoder):
    def default(self, obj: JSONEncodable | JSONSerializable) -> JSONEncodable:
        to_json = getattr(obj, "__json__", None)
        return to_json() if callable(to_json) else super().default(obj)


@dataclass
class SubmissionValueVariablesState:
    submission: Submission
    _variables: dict[str, SubmissionValueVariable] | None = field(
        init=False, default=None
    )
    _static_data: dict[str, Any] | None = field(init=False, default=None)

    @property
    def variables(self) -> dict[str, SubmissionValueVariable]:
        if not self._variables:
            self._variables = self.collect_variables()
        return self._variables

    @property
    def saved_variables(self) -> dict[str, SubmissionValueVariable]:
        return {
            variable_key: variable
            for variable_key, variable in self.variables.items()
            if variable.pk
        }

    def get_variable(self, key: str) -> SubmissionValueVariable:
        return self.variables[key]

    @overload
    def get_data(
        self,
        *,
        as_formio_data: Literal[True],
        submission_step: SubmissionStep | None = None,
        return_unchanged_data: bool = True,
    ) -> FormioData: ...

    @overload
    def get_data(
        self,
        *,
        as_formio_data: Literal[False] = False,
        submission_step: SubmissionStep | None = None,
        return_unchanged_data: bool = True,
    ) -> DataMapping: ...

    def get_data(
        self,
        *,
        as_formio_data: bool = False,
        submission_step: SubmissionStep | None = None,
        return_unchanged_data: bool = True,
    ) -> DataMapping | FormioData:
        """
        Return the values of the dynamic variables in the submission.

        :arg as_formio_data: set to ``True`` to get the :class:`FormioData`
          datastructure instead of the underlying nested dictionaries.
        """
        submission_variables = self.saved_variables
        if submission_step:
            submission_variables = self.get_variables_in_submission_step(
                submission_step, include_unsaved=False
            )

        formio_data = FormioData()
        for variable_key, variable in submission_variables.items():
            if (
                variable.value is None
                and variable.form_variable
                and variable.value == variable.form_variable.initial_value
                and not return_unchanged_data
            ):
                continue

            if variable.source != SubmissionValueVariableSources.sensitive_data_cleaner:
                formio_data[variable_key] = variable.value
        return formio_data if as_formio_data else formio_data.data

    def get_variables_in_submission_step(
        self,
        submission_step: SubmissionStep,
        include_unsaved=True,
    ) -> dict[str, SubmissionValueVariable]:
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

    def collect_variables(self) -> dict[str, SubmissionValueVariable]:
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
                key=variable_key,
                value=form_variable.get_initial_value(),
                is_initially_prefilled=(form_variable.prefill_plugin != ""),
            )
            unsaved_submission_var.form_variable = form_variable
            all_submission_variables[variable_key] = unsaved_submission_var

        return all_submission_variables

    def remove_variables(self, keys: list) -> None:
        for key in keys:
            if key in self._variables:
                del self._variables[key]

    def _get_static_data(self, other_registry: VariablesRegistry | None = None):
        return {
            variable.key: variable.initial_value
            for variable in get_static_variables(
                submission=self.submission,
                variables_registry=other_registry,
            )
        }

    def get_static_data(
        self, other_registry: VariablesRegistry | None = None
    ) -> JSONObject:
        # Ensure we do not accidentally cache the non-default registry
        if other_registry is not None:
            return self._get_static_data(other_registry=other_registry)
        if self._static_data is None:
            self._static_data = self._get_static_data()
        return self._static_data

    static_data = get_static_data  # DeprecationWarning

    def get_prefill_variables(self) -> list[SubmissionValueVariable]:
        prefill_vars = []
        for variable in self.variables.values():
            if not variable.is_initially_prefilled:
                continue
            prefill_vars.append(variable)
        return prefill_vars

    def save_prefill_data(self, data: dict[str, Any]) -> None:
        # The way we retrieve the variables has been changed here, since
        # the new architecture of the prefill module requires access to all the
        # variables at this point (the previous implementation with
        # self.get_prefill_variables() gave us access to the component variables
        # and not the user_defined ones).
        variables_to_create: list[SubmissionValueVariable] = []
        for variable in self.variables.values():
            if variable.key not in data:
                continue

            variable.value = data[variable.key]
            variable.source = SubmissionValueVariableSources.prefill
            variables_to_create.append(variable)

        SubmissionValueVariable.objects.bulk_create(variables_to_create)

    def set_values(self, data: DataMapping) -> None:
        """
        Apply the values from ``data`` to the current state of the variables.

        This does NOT persist the values, it only mutates the value instances in place.
        The ``data`` structure maps variable key and (new) values to set on the
        variables in the state.

        :arg data: mapping of variable key to value.

        .. todo:: apply variable.datatype/format to obtain python objects? This also
           needs to properly serialize back to JSON though!
        """
        formio_data = FormioData(data)
        for key, variable in self.variables.items():
            new_value = formio_data.get(key, default=empty)
            if new_value is empty:
                continue
            variable.value = new_value


class SubmissionValueVariableManager(models.Manager):
    def bulk_create_or_update_from_data(
        self,
        data: DataMapping,
        submission: Submission,
        submission_step: SubmissionStep | None = None,
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
        formio_data = FormioData(data)
        for key, variable in submission_variables.items():
            try:
                variable.value = formio_data[key]
            except KeyError:
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
    key = models.TextField(
        verbose_name=_("key"),
        help_text=_("Key of the variable"),
    )
    value = models.JSONField(
        verbose_name=_("value"),
        help_text=_("The value of the variable"),
        null=True,
        blank=True,
        encoder=ValueEncoder,
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

    form_variable: FormVariable | None = None

    class Meta:
        verbose_name = _("Submission value variable")
        verbose_name_plural = _("Submission values variables")
        unique_together = (("submission", "key"),)

    def __str__(self):
        return _("Submission value variable {key}").format(key=self.key)

    def to_python(self) -> Any:
        """
        Deserialize the value into the appropriate python type.

        TODO: for dates/datetimes, we rely on our django settings for timezone
        information, however - formio submission does send the user's configured
        timezone as metadata, which we can store on the submission/submission step
        to correctly interpret the data. For the time being, this is not needed yet
        as we focus on NL first.
        """
        if self.value is None:
            return None

        # it's possible a submission value variable exists without the form variable
        # being present, e.g. existing submissions for which the form is modified after
        # the submission is created (like removing a form step, which cascade deletes
        # the related form variables).
        # In those situations, we can't do anything meaningful.
        if self.form_variable is None:
            logger.debug(
                "No form variable information available for variable with key %s in "
                "submission value variable %r.",
                self.key,
                self.pk,
                extra={
                    "key": self.key,
                    "submission_id": self.submission_id,
                },
            )
            return self.value

        # we expect JSON types to have been properly stored (and thus not as string!)
        data_type = self.form_variable.data_type
        if data_type in (
            FormVariableDataTypes.string,
            FormVariableDataTypes.boolean,
            FormVariableDataTypes.object,
            FormVariableDataTypes.int,
            FormVariableDataTypes.float,
            FormVariableDataTypes.array,
        ):
            return self.value

        if self.value and data_type == FormVariableDataTypes.date:
            if isinstance(self.value, date):
                return self.value
            formatted_date = format_date_value(self.value)
            naive_date = parse_date(formatted_date)
            if naive_date is not None:
                aware_date = timezone.make_aware(datetime.combine(naive_date, time.min))
                return aware_date.date()

            maybe_naive_datetime = parse_datetime(self.value)
            if maybe_naive_datetime is None:
                return

            if timezone.is_aware(maybe_naive_datetime):
                return maybe_naive_datetime.date()
            return timezone.make_aware(maybe_naive_datetime).date()

        if self.value and data_type == FormVariableDataTypes.datetime:
            if isinstance(self.value, datetime):
                return self.value
            maybe_naive_datetime = parse_datetime(self.value)
            if maybe_naive_datetime is None:
                return

            if timezone.is_aware(maybe_naive_datetime):
                return maybe_naive_datetime
            return timezone.make_aware(maybe_naive_datetime)

        if self.value and data_type == FormVariableDataTypes.time:
            return parse_time(self.value)

        return self.value
