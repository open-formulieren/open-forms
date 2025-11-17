from typing import Any

from django.utils.translation import gettext as _

from glom import assign
from json_logic.meta import JSONLogicExpression, Operation
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.formio.utils import iter_components
from openforms.formio.variables import validate_configuration
from openforms.typing import JSONObject
from openforms.utils.json_logic.api.validators import JsonLogicValidator
from openforms.variables.service import get_static_variables

from ..validation.registry import register as formio_validators_registry


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
        tree = JSONLogicExpression.from_expression(expression).as_tree()
        assert isinstance(tree, Operation)

        # Check that the first operator includes a 'var'
        first_operand = tree.arguments[0]
        is_date_or_datetime_operand = self._is_date_or_datetime_operand(first_operand)
        if not isinstance(first_operand, Operation) or (
            first_operand.operator != "var" and not is_date_or_datetime_operand
        ):
            raise serializers.ValidationError(
                {
                    self.trigger_field: ErrorDetail(self.message, code=self.code),
                }
            )

        self.validate_trigger_values(tree, data, serializer)

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

    def _is_date_or_datetime_operand(self, operand: Any) -> bool:
        return (
            isinstance(operand, Operation)
            and (operand.operator == "date" or operand.operator == "datetime")
            and isinstance(operand.arguments[0], Operation)
            and operand.arguments[0].operator == "var"
        )

    def validate_trigger_values(self, logic_test: Operation, data, serializer):
        """
        Validate that any operand with {"var": "<component name>"} points to a valid component in the form
        """
        form = get_from_serializer_data_or_instance(self.form_field, data, serializer)

        # some data missing, can't perform check
        if not form:
            return

        for operand in logic_test.arguments:
            if not isinstance(operand, Operation):
                continue

            if operand.operator == "var":
                needle = operand.arguments[0]
            elif self._is_date_or_datetime_operand(operand):
                first_arg = operand.arguments[0]
                assert isinstance(first_arg, Operation)
                needle = first_arg.arguments[0]
            else:
                continue

            assert isinstance(needle, str)

            if needle == "":
                raise serializers.ValidationError(
                    {
                        self.trigger_field: ErrorDetail(
                            _("The variable cannot be empty."),
                            code=self.code,
                        ),
                    }
                )

            # Check if the trigger references a static variable
            needle_bits = needle.split(".")
            for variable in get_static_variables():
                if needle_bits[0] == variable.key:
                    return

            form_variables = serializer.context["form_variables"]
            if variable_related_to_form := form_variables.get(needle) is None:
                alternative_needle = ".".join(needle_bits[:-1])
                variable_related_to_form = form_variables.get(alternative_needle)

            if variable_related_to_form is None:
                raise serializers.ValidationError(
                    {
                        self.trigger_field: ErrorDetail(
                            _("The specified variable is not related to the form"),
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
        for component in iter_components(configuration=configuration, recursive=True):
            if not (component_type := component.get("type")):
                continue

            if component_type not in formio_validators_registry:
                continue

            validator = formio_validators_registry[component_type]
            # may raise a :class:`django.core.exceptions.ValidationError`
            validator(component)


class FormLogicTriggerFromStepFormValidator:
    requires_context = True

    def __call__(self, attrs: dict, serializer: serializers.Serializer):
        trigger_from_step = get_from_serializer_data_or_instance(
            "trigger_from_step", attrs, serializer
        )
        form = get_from_serializer_data_or_instance("form", attrs, serializer)
        if not form or not trigger_from_step:
            return

        if trigger_from_step.form != form:
            raise serializers.ValidationError(
                {
                    "trigger_from_step": serializers.ErrorDetail(
                        _(
                            "You must specify a step that belongs to the same form as the logic rule itself."
                        ),
                        code="invalid",
                    )
                }
            )


class FormStepIsApplicableIfFirstValidator:
    def __call__(self, attrs: dict):
        if not attrs.get("is_applicable", True) and attrs.get("order") == 0:
            raise serializers.ValidationError(
                {
                    "is_applicable": serializers.ErrorDetail(
                        _("First form step must be applicable."),
                        code="invalid",
                    ),
                }
            )


def validate_template_expressions(configuration: JSONObject) -> None:
    """
    Validate that any template expressions in supported properties are correct.

    This runs syntax validation on template fragments inside Formio configuration
    objects.
    """
    errored_components = validate_configuration(configuration)
    if not errored_components:
        return

    all_errors = {}
    error = ErrorDetail(
        _("There are template syntax errors in the expression."),
        code="invalid-template-syntax",
    )
    for path in errored_components.values():
        assign(all_errors, path, error, missing=dict)
    raise serializers.ValidationError(all_errors)
