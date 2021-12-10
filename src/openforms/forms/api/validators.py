from typing import Any

from django.utils.translation import gettext as _

from json_logic import jsonLogic
from rest_framework import serializers

from openforms.typing import JSONObject
from openforms.utils.json_logic import JsonLogicTest

from ..validation.registry import register as formio_validators_registry


class JsonLogicValidator:
    """Validate that a json object is a valid jsonLogic expression"""

    def __call__(self, value: dict):
        try:
            jsonLogic(value)
        except ValueError:
            raise serializers.ValidationError(_("Invalid JSON logic."), code="invalid")


class JsonLogicTriggerValidator(JsonLogicValidator):
    """
    Validate that the jsonLogic expression is a valid submission data trigger.

    JSON Logic expressions used as triggers must refer to form components to be
    considered valid and usable.
    """

    code = "invalid"
    message = _('The first operand must be a `{"var": "<componentKey>"}` expression.')

    def __call__(self, expression: dict) -> None:
        # ensure that the expression itself is valid
        super().__call__(expression)

        # at first instance, we don't support nested logic. Once we do, this will need
        # to be adapted so that we only check primitives.
        logic_test = JsonLogicTest.from_expression(expression)

        first_operand = logic_test.values[0]
        is_date_operand = (
            first_operand.operator == "date"
            and isinstance(first_operand.values[0], JsonLogicTest)
            and first_operand.values[0].operator == "var"
        )
        if not isinstance(first_operand, JsonLogicTest) or (
            first_operand.operator != "var" and not is_date_operand
        ):
            raise serializers.ValidationError(self.message, code=self.code)


class JsonLogicTriggerComponentValidator:
    """
    Validate that the trigger expression references a valid form component.

    This validator assumes that the trigger expression has been validated, e.g. with
    :class:`JsonLogicTriggerValidator`.
    """

    default_message = _("The specified component is not present in the form definition")
    default_code = "invalid"
    requires_context = True

    def __init__(
        self, trigger_field: str = "json_logic_trigger", form_field: str = "form"
    ):
        self.trigger_field = trigger_field
        self.form_field = form_field

    @staticmethod
    def _get_field_from_data_or_instance(
        field: str, data: dict, serializer: serializers.Serializer
    ) -> Any:
        if not (value := data.get(field)):
            serializer_field = serializer.fields[field]
            value = serializer_field.get_attribute(serializer.instance)
        return value

    def __call__(self, data: dict, serializer: serializers.Serializer) -> None:
        """
        Test that the trigger component is present in the form definition(s).
        """
        form = self._get_field_from_data_or_instance(self.form_field, data, serializer)
        trigger_expression = self._get_field_from_data_or_instance(
            self.trigger_field, data, serializer
        )

        # some data missing, can't perform check
        if not form or not trigger_expression:
            return

        logic_test = JsonLogicTest.from_expression(trigger_expression)
        first_operand = logic_test.values[0]
        if (
            first_operand.operator == "date"
            and isinstance(first_operand.values[0], JsonLogicTest)
            and first_operand.values[0].operator == "var"
        ):
            needle = first_operand.values[0].values[0]
        else:
            needle = first_operand.values[0]
        for component in form.iter_components(recursive=True):
            key = component.get("key")
            if key and key == needle:
                break

            if component.get("type") == "selectboxes":
                needle_bits = needle.split(".")
                key_bits = key.split(".")
                if key_bits == needle_bits[:-1]:
                    break

        # executes if the break was not hit
        else:
            error = serializers.ValidationError(
                self.default_message, code=self.default_code
            )
            raise serializers.ValidationError({self.trigger_field: error})


class FormIOComponentsValidator:
    """
    Run validation on all components in a FormIO JSON schema.

    This invokes a registry of lower-level validators and lets the errors bubble
    up for a pluggable interface.
    """

    def __call__(self, configuration: JSONObject) -> None:
        from ..models import FormDefinition

        instance = FormDefinition()

        for component in instance.iter_components(
            configuration=configuration, recursive=True
        ):
            if not (component_type := component.get("type")):
                continue

            if component_type not in formio_validators_registry:
                continue

            validator = formio_validators_registry[component_type]
            # may raise a :class:`django.core.exceptions.ValidationError`
            validator(component)
