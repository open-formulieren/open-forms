from django.utils.translation import ugettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from ....models import FormLogic
from ...validators import JsonLogicTriggerValidator, JsonLogicValidator
from .action_serializers import LogicComponentActionSerializer


class FormLogicBaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        fields = (
            "uuid",
            "url",
            "form",
            "json_logic_trigger",
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "form": {
                "view_name": "api:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
            "json_logic_trigger": {
                "help_text": _(
                    "The trigger expression to determine if the actions should execute "
                    "or not. Note that this must be a valid JsonLogic expression, and "
                    "the first operand must be a reference to a component in the form."
                ),
                "validators": [JsonLogicValidator()],
            },
        }
        validators = [
            JsonLogicTriggerValidator("json_logic_trigger"),
        ]


class FormLogicSerializer(FormLogicBaseSerializer, OrderedModelSerializer):
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("Actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    class Meta(FormLogicBaseSerializer.Meta):
        model = FormLogic
        fields = FormLogicBaseSerializer.Meta.fields + (
            "order",
            "actions",
            "is_advanced",
        )
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:form-logics-detail",
                "lookup_field": "uuid",
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
