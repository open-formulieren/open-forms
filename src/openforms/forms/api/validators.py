from django.utils.translation import gettext as _

from json_logic import jsonLogic
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.utils import get_from_serializer_data_or_instance
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
    requires_context = True

    def __init__(
        self,
        trigger_field: str = "json_logic_trigger",
        form_field: str = "form",
        is_advanced_field: str = "is_advanced",
    ):
        self.trigger_field = trigger_field
        self.form_field = form_field
        self.is_advanced_field = is_advanced_field

    def __call__(self, data: dict, serializer: serializers.Serializer) -> None:
        expression: dict = get_from_serializer_data_or_instance(
            self.trigger_field, data, serializer
        )

        # ensure that the expression itself is valid
        super().__call__(expression)

        # check if we need to allow a complex expression through because it's advanced logic
        if self._is_advanced_logic(data, serializer):
            return

        # at first instance, we don't support nested logic. Once we do, this will need
        # to be adapted so that we only check primitives.
        logic_test = JsonLogicTest.from_expression(expression)

        first_operand = logic_test.values[0]
        is_date_operand = (
            isinstance(first_operand, JsonLogicTest)
            and first_operand.operator == "date"
            and isinstance(first_operand.values[0], JsonLogicTest)
            and first_operand.values[0].operator == "var"
        )
        if not isinstance(first_operand, JsonLogicTest) or (
            first_operand.operator != "var" and not is_date_operand
        ):
            raise serializers.ValidationError(
                {
                    self.trigger_field: ErrorDetail(self.message, code=self.code),
                }
            )

        # finally, validate that it points to a valid component in the form
        form = get_from_serializer_data_or_instance(self.form_field, data, serializer)

        # some data missing, can't perform check
        if not form:
            return

        if is_date_operand:
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
            raise serializers.ValidationError(
                {
                    self.trigger_field: ErrorDetail(
                        _(
                            "The specified component is not present in the form definition"
                        ),
                        code=self.code,
                    ),
                }
            )

    def _is_advanced_logic(
        self, data: dict, serializer: serializers.Serializer
    ) -> bool:
        # check if we need to allow a complex expression through because it's advanced logic
        if self.is_advanced_field in serializer.fields:
            is_advanced = get_from_serializer_data_or_instance(
                self.is_advanced_field, data, serializer
            )
            if is_advanced:
                return True
        return False


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
