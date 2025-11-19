from django.utils.translation import gettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.fields import RelatedFieldFromContext
from openforms.api.serializers import ListWithChildSerializer

from ....logic_analysis import (
    create_graph,
    detect_cycles,
    resolve_order_with_step,
)
from ....models import Form, FormLogic, FormStep
from ...validators import (
    FormLogicTriggerFromStepFormValidator,
    JsonLogicTriggerValidator,
    JsonLogicValidator,
)
from .action_serializers import LogicComponentActionSerializer


# TODO-2409: with price logic gone, I think we can get rid of this base serializer?
class FormLogicBaseSerializer(serializers.HyperlinkedModelSerializer):
    form = RelatedFieldFromContext(
        queryset=Form.objects.all(),
        view_name="api:form-detail",
        lookup_field="uuid",
        lookup_url_kwarg="uuid_or_slug",
        required=True,
        context_name="forms",
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        related_field = self.Meta.model._meta.get_field("form")
        self.fields["form"].help_text = related_field.help_text
        self.fields["form"].label = related_field.verbose_name


class FormLogicListSerializer(ListWithChildSerializer):
    child_serializer_class = (
        "openforms.forms.api.serializers.logic.form_logic.FormLogicSerializer"
    )

    # TODO-2409: might also be able to set the graph validator like this, instead of
    #  overriding the `validate` method.
    # class Meta:
    #     validators = [FormLogicGraphValidator()]

    def validate(self, data):
        # This will only run when the logic rules have passed individual serializer
        # validation, so we can initialize model instances here.
        # Note: model instances without a pk are not hashable, which is required to use
        # them in the graph, so we set it to the order manually. These rules will just
        # live in memory, so it will not result in conflicts with existing rules.
        rules = [FormLogic(**rule_data, pk=rule_data["order"]) for rule_data in data]

        graph = create_graph(rules)
        cycles = detect_cycles(graph)
        if cycles:
            # TODO-2409: this should raise the errors on the affected rules
            raise serializers.ValidationError("Cycles detected in logic rules")

        # add_missing_steps(graph)
        new_rule_order = resolve_order_with_step(graph)

        # Reorder the incoming data according to the determined order.
        data_new, steps = [], []
        for rule in new_rule_order:
            # We can get the original rule data by using the order as an index
            rule_data = data[rule.order]
            steps.append(list(rule.steps))
            data_new.append(rule_data)

        # Saving it to the context here to avoid determining the steps again when
        # assigning them to the `form_steps` model property (it is an expensive
        # operation, fow now anyway).
        self.context["steps_for_each_rule"] = steps

        return super().validate(data_new)

    def create(self, validated_data):
        rules = super().create(validated_data)

        # It is not allowed to directly set a many-to-many relationship, so we have to
        # do it after the FormLogic instances have been created.
        for rule, step_list in zip(
            rules, self.context["steps_for_each_rule"], strict=False
        ):
            rule.form_steps.set(step_list)

        return rules


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
    # form_steps = NestedHyperlinkedRelatedField(
    #     required=False,
    #     allow_null=True,
    #     many=True,
    #     queryset=FormStep.objects,
    #     view_name="api:form-steps-detail",
    #     lookup_field="uuid",
    #     parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
    #     label=_("form steps"),
    #     help_text=_(
    #         "When set, the trigger will only be checked once the specified step is reached. "
    #         "This means the rule will never trigger for steps before the specified trigger step. "
    #         "If unset, the trigger will always be checked."
    #     ),
    # )

    class Meta(FormLogicBaseSerializer.Meta):
        model = FormLogic
        list_serializer_class = FormLogicListSerializer
        fields = FormLogicBaseSerializer.Meta.fields + (
            "description",
            "order",
            "trigger_from_step",
            "actions",
            "is_advanced",
            # "form_steps",
        )
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
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
        validators = FormLogicBaseSerializer.Meta.validators + [
            FormLogicTriggerFromStepFormValidator()
        ]
