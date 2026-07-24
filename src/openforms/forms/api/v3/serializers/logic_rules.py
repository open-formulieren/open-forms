import uuid

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from ....api.serializers.logic.action_serializers import (
    LOGIC_ACTION_TYPES_REQUIRING_COMPONENT,
    LOGIC_ACTION_TYPES_REQUIRING_FORM_STEP_UUID,
    LOGIC_ACTION_TYPES_REQUIRING_VARIABLE,
    LogicActionPolymorphicSerializer,
    _join_action_types,
)
from ....models import FormLogic
from ...validators import (
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)


@extend_schema_serializer(component_name="LogicComponentActionV3Serializer")
class LogicComponentActionSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(
        read_only=True,
        default=uuid.uuid4,
        label=_("UUID"),
    )
    component = serializers.CharField(
        required=False,
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
        required=False,
        allow_blank=True,
        label=_("Key of the target variable"),
        help_text=_(
            "Key of the target variable whose value will be changed. This field is "
            "required for the action types {action_types} - otherwise it's optional."
        ).format(
            action_types=_join_action_types(LOGIC_ACTION_TYPES_REQUIRING_VARIABLE)
        ),
    )
    form_step_slug = serializers.CharField(
        allow_null=True,
        allow_blank=True,
        required=False,
        label=_("form step slug"),
        help_text=_(
            "The slug of the form step that will be affected by the action. This field "
            "is required for action types {action_types} - otherwise it's optional. We "
            "deliberately use the slug instead of the uuid because the uuid is not fixed, "
            "as we create from scratch the form steps dusring form update."
        ).format(
            action_types=_join_action_types(LOGIC_ACTION_TYPES_REQUIRING_FORM_STEP_UUID)
        ),
    )
    action = LogicActionPolymorphicSerializer()


@extend_schema_serializer(component_name="FormLogicV3Serializer")
class FormLogicSerializer(OrderedModelSerializer):
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    class Meta:
        model = FormLogic
        fields = (
            "uuid",
            "json_logic_trigger",
            "description",
            "order",
            "actions",
            "is_advanced",
        )
        extra_kwargs = {
            "uuid": {"read_only": True},
            "json_logic_trigger": {
                "help_text": _(
                    "The trigger expression to determine if the actions should execute "
                    "or not. Note that this must be a valid JsonLogic expression, and "
                    "the first operand must be a reference to a variable in the form."
                ),
                "validators": [JsonLogicValidator()],
            },
            "order": {
                "read_only": False,
                "help_text": _(
                    "Order of the rule relative to the form it belongs to. Logic rules "
                    "are evaluated in this order. Note that specifying a value for the "
                    "order here will cause the rules before/after this rule to be "
                    "re-calculated."
                ),
            },
        }
        validators = [JsonLogicTriggerValidator("json_logic_trigger")]
