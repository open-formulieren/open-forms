from typing import Any, Union

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


class JsonLogicActionValueValidator(JsonLogicValidator):
    code = "invalid"
    message = _("This field needs to refer to a form component")

    def __call__(self, value: Union[dict, str]) -> None:
        if isinstance(value, str):
            return

        # ensure that the expression itself is valid
        super().__call__(value)

        expression = JsonLogicTest.from_expression(value)

        if expression.values[0] == "":
            raise serializers.ValidationError(ErrorDetail(self.message, code=self.code))


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

        # Check that the first operator includes a 'var'
        first_operand = logic_test.values[0]
        is_date_operand = self._is_date_operand(first_operand)
        if not isinstance(first_operand, JsonLogicTest) or (
            first_operand.operator != "var" and not is_date_operand
        ):
            raise serializers.ValidationError(
                {
                    self.trigger_field: ErrorDetail(self.message, code=self.code),
                }
            )

        self.validate_trigger_values(logic_test, data, serializer)

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

    def _is_date_operand(self, operand: Any) -> bool:
        return (
            isinstance(operand, JsonLogicTest)
            and operand.operator == "date"
            and isinstance(operand.values[0], JsonLogicTest)
            and operand.values[0].operator == "var"
        )

    def validate_trigger_values(self, logic_test, data, serializer):
        """
        Validate that any operand with {"var": "<component name>"} points to a valid component in the form
        """
        for index, operand in enumerate(logic_test.values):
            if not isinstance(operand, JsonLogicTest):
                continue

            form = get_from_serializer_data_or_instance(
                self.form_field, data, serializer
            )

            # some data missing, can't perform check
            if not form:
                return

            if operand.operator == "var":
                needle = operand.values[0]
            elif self._is_date_operand(operand):
                needle = operand.values[0].values[0]
            else:
                continue

            if needle == "":
                raise serializers.ValidationError(
                    {
                        self.trigger_field: ErrorDetail(
                            _("The component cannot be empty."),
                            code=self.code,
                        ),
                    }
                )

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
