import uuid
from collections import Counter
from datetime import date

from django.utils.translation import gettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from drf_spectacular.utils import extend_schema_serializer
from json_logic.typing import Primitive
from rest_framework import serializers

from openforms.api.serializers import DummySerializer
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.json_logic.api.validators import JsonLogicValidator
from openforms.variables.constants import FormVariableDataTypes

from ....constants import (
    LOGIC_ACTION_TYPES_REQUIRING_COMPONENT,
    LOGIC_ACTION_TYPES_REQUIRING_FORM_STEP_UUID,
    LOGIC_ACTION_TYPES_REQUIRING_VARIABLE,
    LogicActionTypes,
    PropertyTypes,
)
from .fields import ActionFormStepUUIDField


class ComponentPropertySerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("property key"),
        help_text=_(
            "The Form.io component property to alter, identified by `component.key`"
        ),
    )
    type = serializers.ChoiceField(
        label=_("type"),
        help_text=_("The type of the value field"),
        choices=PropertyTypes.choices,
    )


class LogicPropertyActionSerializer(serializers.Serializer):
    property = ComponentPropertySerializer()
    state = serializers.JSONField(
        label=_("value of the property"),
        help_text=_(
            "Valid JSON determining the new value of the specified property. For example: `true` or `false`."
        ),
    )

    def validate_state(self, value):
        if value == "":
            raise serializers.ValidationError(
                self.fields["state"].error_messages["null"],
                code="blank",
            )
        return value


class LogicValueActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("Value"),
        help_text=_(
            "A valid JsonLogic expression describing the value. This may refer to "
            "(other) Form.io components."
        ),
        validators=[JsonLogicValidator()],
    )


class SynchronizeDataMappingSerializer(serializers.Serializer):
    property = serializers.CharField(
        label=_("Property that needs mapping."), required=True
    )
    component_key = FormioVariableKeyField(
        label=_("Key of the component variable."),
        required=True,
    )


class SynchronizeVariablesActionConfigSerializer(serializers.Serializer):
    identifier_variable = FormioVariableKeyField(
        required=True,
        allow_blank=False,
        label=_("Key of the form variable that will be used as the identifier (BSN)."),
    )
    source_variable = FormioVariableKeyField(
        label=_("Key of the form variable that will be used as the source."),
        required=True,
        allow_blank=False,
    )
    destination_variable = FormioVariableKeyField(
        label=_("Key of the form variable that will be used as the destination."),
        required=True,
        allow_blank=False,
    )
    data_mappings = SynchronizeDataMappingSerializer(
        label=_("Synchronize variables mapping"),
        many=True,
        min_length=1,  # pyright: ignore[reportCallIssue]
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        mappings = attrs.get("data_mappings")
        mappings_component_keys = [m["component_key"] for m in mappings]
        identifier_key = attrs["identifier_variable"]

        counts = Counter(mappings_component_keys)
        duplicates = [key for key, count in counts.items() if count > 1]
        if duplicates:
            raise serializers.ValidationError(
                {"data_mappings": _("A variable cannot be mapped multiple times.")}
            )

        if identifier_key not in mappings_component_keys:
            raise serializers.ValidationError(
                {
                    "data_mappings": _(
                        "No mapping for the identifier variable was found."
                    )
                }
            )

        return attrs


class SynchronizeVariablesActionSerializer(serializers.Serializer):
    config = SynchronizeVariablesActionConfigSerializer(label=_("Configuration"))


class LogicFetchActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("service_fetch_configuration"),
    )


class VariableMappingSerializer(serializers.Serializer):
    form_variable = FormioVariableKeyField(
        required=True,
        label=_("Key of the form variable."),
    )
    dmn_variable = serializers.CharField(
        required=True, label=_("DMN input parameter name.")
    )


class DMNEvaluateActionConfigSerializer(serializers.Serializer):
    plugin_id = serializers.CharField(
        label=_("Plugin ID"), required=True, allow_blank=False
    )
    decision_definition_id = serializers.CharField(
        label=_("Decision definition ID"), required=True, allow_blank=False
    )
    decision_definition_version = serializers.CharField(
        label=_("Decision definition version"),
        required=False,
        allow_blank=True,
        default="",
    )
    input_mapping = VariableMappingSerializer(many=True, label=_("Input mapping"))
    output_mapping = VariableMappingSerializer(many=True, label=_("Output mapping"))


class DMNEvaluateActionSerializer(serializers.Serializer):
    config = DMNEvaluateActionConfigSerializer(label=_("Configuration"))


class LogicSetRegistrationBackendActionSerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("registration_backend_key"),
        allow_blank=False,
    )


class LogicActionPolymorphicSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(
        choices=LogicActionTypes.choices,
        label=_("Type"),
        help_text=_("Action type for this particular action."),
    )

    discriminator_field = "type"
    serializer_mapping = {
        str(LogicActionTypes.disable_next): DummySerializer,
        str(LogicActionTypes.property): LogicPropertyActionSerializer,
        str(LogicActionTypes.step_not_applicable): DummySerializer,
        str(LogicActionTypes.step_applicable): DummySerializer,
        str(LogicActionTypes.variable): LogicValueActionSerializer,
        str(LogicActionTypes.fetch_from_service): LogicFetchActionSerializer,
        str(LogicActionTypes.evaluate_dmn): DMNEvaluateActionSerializer,
        str(
            LogicActionTypes.set_registration_backend
        ): LogicSetRegistrationBackendActionSerializer,
        str(
            LogicActionTypes.synchronize_variables
        ): SynchronizeVariablesActionSerializer,
    }


def _join_action_types(action_types):
    return f"`{'`, `'.join(sorted(action_types))}`"


@extend_schema_serializer(deprecate_fields=["form_step"])
class LogicComponentActionSerializer(serializers.Serializer):
    # TODO: validate that the component is present on the form
    uuid = serializers.UUIDField(
        read_only=True,
        default=uuid.uuid4,
        label=_("UUID"),
    )
    component = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Form.io component"),
        help_text=_(
            "Key of the Form.io component that the action applies to. This field is "
            "required for the action types {action_types} - otherwise it's optional."
        ).format(
            action_types=_join_action_types(LOGIC_ACTION_TYPES_REQUIRING_COMPONENT)
        ),
    )
    variable = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Key of the target variable"),
        help_text=_(
            "Key of the target variable whose value will be changed. This field is "
            "required for the action types {action_types} - otherwise it's optional."
        ).format(
            action_types=_join_action_types(LOGIC_ACTION_TYPES_REQUIRING_VARIABLE)
        ),
    )
    form_step_uuid = ActionFormStepUUIDField(
        allow_null=True,
        required=False,  # validated against the action.type
        label=_("form step"),
        help_text=_(
            "The UUID of the form step that will be affected by the action. This field "
            "is required for action types {action_types} - otherwise it's optional."
        ).format(
            action_types=_join_action_types(LOGIC_ACTION_TYPES_REQUIRING_FORM_STEP_UUID)
        ),
    )
    action = LogicActionPolymorphicSerializer()

    def validate(self, attrs: dict) -> dict:
        """
        1. Check that the component is supplied depending on the action type.
        2. Check that the value for date variables has the right format
        """
        action_type = attrs.get("action", {}).get("type")
        action_value = attrs.get("action", {}).get("value")
        component = attrs.get("component")

        form_step_uuid = attrs.get("form_step_uuid")
        variable = attrs.get("variable")

        if (
            action_type
            and action_type in LOGIC_ACTION_TYPES_REQUIRING_COMPONENT
            and not component
        ):
            raise serializers.ValidationError(
                {"component": self.fields["component"].error_messages["blank"]},
                code="blank",
            )

        if (
            action_type
            and action_type in LOGIC_ACTION_TYPES_REQUIRING_VARIABLE
            and not variable
        ):
            raise serializers.ValidationError(
                {"variable": self.fields["variable"].error_messages["blank"]},
                code="blank",
            )

        # validate variable exists
        if action_type == LogicActionTypes.variable:
            form_var = self.context["form_variables"].variables.get(variable)
            if form_var is None:
                raise serializers.ValidationError(
                    {
                        "variable": _("The variable {varname} does not exist.").format(
                            varname=variable
                        ),
                    }
                )

        # validate format of value for date variable
        if action_type == LogicActionTypes.variable and isinstance(
            action_value, Primitive
        ):
            form_var = self.context["form_variables"].variables[variable]

            if form_var.data_type == FormVariableDataTypes.date:
                try:
                    # type check muted since we handle it at runtime
                    date.fromisoformat(
                        action_value  # pyright: ignore[reportArgumentType]
                    )
                except (ValueError, TypeError) as ex:
                    raise serializers.ValidationError(
                        {
                            "action": {
                                "value": _(
                                    "Value for date variable must be a string in the "
                                    "format yyyy-mm-dd (e.g. 2023-07-03)"
                                ),
                            }
                        },
                    ) from ex

        if (
            action_type in LOGIC_ACTION_TYPES_REQUIRING_FORM_STEP_UUID
            and not form_step_uuid
        ):
            raise serializers.ValidationError(
                {
                    "form_step_uuid": self.fields["form_step_uuid"].error_messages[
                        "null"
                    ]
                },
                code="blank",
            )

        return attrs
