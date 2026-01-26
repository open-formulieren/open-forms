from django.utils.translation import gettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.fields import RelatedFieldFromContext
from openforms.api.serializers import ListWithChildSerializer

from ....models import Form, FormLogic, FormStep
from ...validators import (
    FormLogicTriggerFromStepFormValidator,
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)
from .action_serializers import LogicComponentActionSerializer


class FormLogicListSerializer(ListWithChildSerializer):
    child_serializer_class = (
        "openforms.forms.api.serializers.logic.form_logic.FormLogicSerializer"
    )


class FormLogicSerializer(
    serializers.HyperlinkedModelSerializer, OrderedModelSerializer
):
    form = RelatedFieldFromContext(
        queryset=Form.objects.all(),
        view_name="api:form-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid_or_slug",
        required=True,
        context_name="forms",
    )
    trigger_from_step = NestedHyperlinkedRelatedField(
        required=False,
        allow_null=True,
        queryset=FormStep.objects,
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
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

    class Meta:
        model = FormLogic
        list_serializer_class = FormLogicListSerializer
        fields = (
            "uuid",
            "url",
            "form",
            "json_logic_trigger",
            "description",
            "order",
            "trigger_from_step",
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
            "url": {
                "view_name": "api:form-logic-rules",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
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
            FormLogicTriggerFromStepFormValidator(),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        related_field = self.Meta.model._meta.get_field("form")
        self.fields["form"].help_text = related_field.help_text
        self.fields["form"].label = related_field.verbose_name
