from typing import Literal

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import JSONField

from openforms.formio.service import normalize_value_for_component
from openforms.forms.models import Form

from ..exceptions import FormMaintenance
from ..models import SubmissionStep


class ValidatePrefillData:
    code = "invalidPrefilledField"
    default_message = _("The prefill data may not be altered.")
    requires_context = True

    def __call__(self, data: dict, field: JSONField):
        instance: SubmissionStep = field.parent.instance
        assert instance._form_logic_evaluated, "Logic must be evaluated"
        prefill_data = instance.submission.get_prefilled_data()

        errors = {}
        for component in instance.form_step.iter_components():
            if "prefill" not in component or component["prefill"]["plugin"] == "":
                continue

            if not component["disabled"]:
                continue

            # match on key
            if not (component_key := component.get("key")):
                continue

            # in case the component or its parent component is hidden the key will not be
            # part of the data.
            if component_key not in data:
                continue

            original_prefill_value = prefill_data.get(component_key)
            if original_prefill_value is None:
                # the value will be `None` if there is no actual prefill data available, so there is nothing to compare to. This
                # especially applies to test-environments without real prefill-connections.
                continue

            prefill_value = normalize_value_for_component(
                component, original_prefill_value
            )
            new_value = data.get(component_key)
            if new_value != prefill_value:
                errors[component_key] = serializers.ErrorDetail(
                    self.default_message, code=self.code
                )

        if errors:
            raise serializers.ValidationError(errors)


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
