from typing import Literal

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import JSONField

from formio_types import (
    AddressNL,
    Checkbox,
    Children,
    Columns,
    Content,
    CosignV1,
    CosignV2,
    Currency,
    CustomerProfile,
    EditGrid,
    Email,
    Fieldset,
    File,
    Iban,
    LicensePlate,
    Map,
    NpFamilyMembers,
    Partners,
    PhoneNumber,
    Radio,
    Select,
    Selectboxes,
    Signature,
    SoftRequiredErrors,
    Textarea,
    Time,
)
from openforms.formio.service import FormioData
from openforms.forms.models import Form
from openforms.submissions.form_logic import evaluate_form_logic

from ..exceptions import FormMaintenance
from ..models import SubmissionStep


class ValidatePrefillData:
    code = "invalidPrefilledField"
    default_message = _("The prefill data may not be altered.")
    requires_context = True

    def __call__(self, data: FormioData, field: JSONField):
        assert field.parent.instance
        instance = field.parent.instance
        assert isinstance(instance, SubmissionStep)
        assert instance.form_step is not None

        # ensure that backend logic is evaluated, which may alter the formio component
        # validation rules. The formio configuration and state are mutated as a side
        # effect. To prevent using an incorrect configuration and/or state later, we
        # need to make sure to reset them to the initial state after validating prefill
        # data.
        # NOTE - we deliberately *don't* pass the client-side ``data`` here for the
        # logic evaluated, as it is untrusted and unvalidated input. This assumes that
        # static variables are used to flip components to readonly/disabled state. If
        # user input is used to perform this flip, the end-user can manipulate this
        # value too and force the logic evaluation to mark the component as not
        # readonly, which beats the point of performing this check.
        state = instance.submission.variables_state
        original_data = state.get_data(include_unsaved=True)
        evaluate_form_logic(instance.submission, step=instance, unsaved_data=None)

        prefilled_data = state.get_prefilled_data()

        errors = {}
        assert instance.form_step is not None
        for component in instance.form_step.form_definition.formio_config:
            # only process components that have prefill configured *and* are not
            # editable (disabled/read-only set to True)
            match component:
                # skip components that don't support prefill
                case (
                    AddressNL()
                    | Checkbox()
                    | Children()
                    | Columns()
                    | Content()
                    | CosignV1()
                    | CosignV2()
                    | Currency()
                    | CustomerProfile()
                    | EditGrid()
                    | Email()
                    | Fieldset()
                    | File()
                    | Iban()
                    | LicensePlate()
                    | Map()
                    | NpFamilyMembers()
                    | Partners()
                    | PhoneNumber()
                    | Radio()
                    | Select()
                    | Selectboxes()
                    | Signature()
                    | SoftRequiredErrors()
                    | Textarea()
                    | Time()
                ):
                    if hasattr(component, "prefill"):  # pragma: no cover
                        raise TypeError(
                            f"Component {component} prefill support unexpectedly ignored!"
                        )
                    continue
                # only consider components that have prefill configured
                case _ if component.prefill is None or not component.prefill.plugin:
                    continue
                # and finally, skip components that are not read-only
                case _ if not component.disabled:
                    continue

            # in case the component or its parent component is hidden the key will not be
            # part of the data.
            if not (component_key := component.key) or component_key not in data:
                continue

            prefill_value = prefilled_data.get(component_key)
            if prefill_value is None:
                # The value will be `None` if there is no actual prefill data available,
                # or if the normalization has failed. E.g., if we receive a "date"
                # '1985', conversion to a date object will result in `None`. There is
                # no use in comparing it to the new value. This especially applies to
                # test-environments without real prefill-connections.
                continue

            # Prefilled values fetched from the state are in native Python types, so
            # we need to convert the new value before doing a comparison.
            new_value = state.variables[component_key].to_python(data[component_key])
            if new_value != prefill_value:
                errors[component_key] = serializers.ErrorDetail(
                    self.default_message, code=self.code
                )

        if errors:
            raise serializers.ValidationError(errors)

        # Reset the configuration and data to the state from before validating prefill.
        state.set_values(original_data)
        instance._form_logic_evaluated = False
        del instance.form_step.form_definition.formio_config


class FormMaintenanceModeValidator:
    code = FormMaintenance.default_code
    message = FormMaintenance.default_detail
    requires_context = True

    def __call__(self, form: Form, field: serializers.RelatedField):
        if (request := field.context.get("request")) is not None:
            # Staff users can start forms that are in maintenance mode
            if request.user.is_staff:
                return
        if form.maintenance_mode:
            raise serializers.ValidationError(self.message, code=self.code)


type StatementFieldName = Literal["ask_privacy_consent", "ask_statement_of_truth"]


class CheckCheckboxAccepted:
    message = _("You must accept this statement.")
    requires_context = True

    ask_statement_field_name: StatementFieldName

    def __init__(self, ask_statement_field_name: StatementFieldName, message):
        self.ask_statement_field_name = ask_statement_field_name
        self.message = message or self.message

    def __call__(self, value: bool, field: serializers.BooleanField):
        form: Form = field.context["submission"].form
        should_statement_be_accepted = form.get_statement_checkbox_required(
            self.ask_statement_field_name
        )
        declaration_valid = value if should_statement_be_accepted else True
        if not declaration_valid:
            raise serializers.ValidationError(self.message, code="required")
