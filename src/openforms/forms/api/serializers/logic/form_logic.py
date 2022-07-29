from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.utils import get_from_serializer_data_or_instance

from ....models import FormLogic, FormStep
from ...validators import (
    FormLogicTriggerFromStepFormValidator,
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)
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
                    "the first operand must be a reference to a variable in the form."
                ),
                "validators": [JsonLogicValidator()],
            },
        }
        validators = [
            JsonLogicTriggerValidator("json_logic_trigger"),
        ]


class FormLogicSerializer(FormLogicBaseSerializer, OrderedModelSerializer):
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

    class Meta(FormLogicBaseSerializer.Meta):
        model = FormLogic
        fields = FormLogicBaseSerializer.Meta.fields + (
            "order",
            "trigger_from_step",
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
        validators = FormLogicBaseSerializer.Meta.validators + [
            FormLogicTriggerFromStepFormValidator()
        ]

    def save(self, **kwargs):
        """
        Manage row-level locks while performing updates.

        Updating the order through the API is sensitive to race conditions, as
        specifying the order for a logic rule causes the _other rules_ to be updated
        as well. Parallel requests affect each other and can lead to unexpected
        calculated order values.

        To guard against this, we wrap the save operation in an atomic transaction,
        but this in turn leads to deadlocks because multiple parallel requests are
        waiting for each other. To mitigate THAT, we lock all the form logic rules for
        the involved form.
        """
        # taken from drf BaseSerializer.save
        validated_data = {**self.validated_data, **kwargs}
        form = get_from_serializer_data_or_instance("form", validated_data, self)
        logic_rules = form.formlogic_set.all()

        with transaction.atomic():
            # evaluate queryset to force row-level locks
            list(logic_rules.select_for_update())
            if self.instance:
                # ensure that we are not looking at stale date if we were waiting for a lock
                self.instance.refresh_from_db()
            return super().save(**kwargs)
