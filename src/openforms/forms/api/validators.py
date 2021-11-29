from django.utils.translation import gettext as _

from json_logic import jsonLogic
from rest_framework import serializers

from openforms.utils.json_logic import JsonLogicTest


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
