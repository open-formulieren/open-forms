from django.utils.translation import ugettext_lazy as _

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


class FormLogicSerializer(FormLogicBaseSerializer):
    actions = LogicComponentActionSerializer(
        many=True,
        label=_("Actions"),
        help_text=_(
            "Actions triggered when the trigger expression evaluates to 'truthy'."
        ),
    )

    class Meta(FormLogicBaseSerializer.Meta):
        model = FormLogic
        fields = FormLogicBaseSerializer.Meta.fields + ("actions", "is_advanced")
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:form-logics-detail",
                "lookup_field": "uuid",
            },
        }
