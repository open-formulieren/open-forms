from typing import Any

from django.core import validators
from django.utils.translation import gettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from openforms.api.serializers import ListWithChildSerializer

from ....models import FormLogic
from ...serializers.logic.action_serializers import LogicComponentActionSerializer
from ...validators import (
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)


class FormLogicListSerializer(ListWithChildSerializer):
    child_serializer_class = (
        "openforms.forms.api.v3.serializers.logic_rules.FormLogicSerializer"
    )


class FormLogicSerializer(OrderedModelSerializer):
    trigger_from_step = serializers.CharField(
        required=False,
        validators=[validators.validate_slug],
        label=_("trigger from step"),
        help_text=_(
            "When set, the trigger will only be checked once the specified step is reached. "
            "This means the rule will never trigger for steps before the specified trigger step. "
            "If unset, the trigger will always be checked."
        ),
    )
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("Actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    form_steps = serializers.ListField(
        child=serializers.CharField(validators=[validators.validate_slug]),
        required=False,
        label=_("form steps"),
        help_text=_(
            "Form steps on which the rule will be executed, determined by logic rule "
            "analysis. Note that this is only relevant when the "
            "`new_logic_evaluation_enabled` feature flag on the form is set to `True`."
        ),
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        validated_data = super().validate(attrs)

        trigger_from_step = validated_data.get("trigger_from_step")
        form_steps = validated_data.get("form_steps", [])

        if trigger_from_step and not form_steps:
            raise serializers.ValidationError(
                {
                    "trigger_from_step": _(
                        "You must specify form steps in order to make use of this field."
                    )
                }
            )
        elif trigger_from_step and trigger_from_step not in form_steps:
            raise serializers.ValidationError(
                {
                    "trigger_from_step": _(
                        "{value} not found in specified form steps."
                    ).format(value=trigger_from_step)
                }
            )
        return validated_data

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = FormLogic
        list_serializer_class = FormLogicListSerializer
        fields = (
            "uuid",
            "json_logic_trigger",
            "description",
            "order",
            "trigger_from_step",
            "actions",
            "is_advanced",
            "form_steps",
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
        validators = [
            JsonLogicTriggerValidator("json_logic_trigger"),
        ]
