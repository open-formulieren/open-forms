from collections import defaultdict

from django.utils.translation import gettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.fields import RelatedFieldFromContext
from openforms.api.serializers import ListWithChildSerializer

from ....logic_analysis import (
    add_missing_steps,
    create_graph,
    detect_cycles,
    resolve_order,
)
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

    def validate(self, attrs):
        if not self.context["form"].new_logic_evaluation_enabled:
            return super().validate(attrs)

        # This will only run when the logic rules have passed individual serializer
        # validation, so we can initialize model instances here.
        # Note: model instances without a pk are not hashable, which is a requirement to
        # use them in the graph, so we assign it manually. These rules will just live in
        # memory, so it will not result in conflicts with existing rules.
        _temporary_rules: list[FormLogic] = [
            FormLogic(**rule_data, pk=i) for i, rule_data in enumerate(attrs)
        ]

        graph = create_graph(_temporary_rules)
        cycles = detect_cycles(graph)
        if cycles:
            msg = _("Rule contains cycles through variable(s): {variables}.")
            errors: defaultdict[str, list[ErrorDetail]] = defaultdict(list)
            for cycle in cycles:
                # Sort to get consistent order in the error message (rules of a cycle do
                # not have a start or end, so the order in which they are processed is
                # not always consistent).
                var_keys = ", ".join(sorted(cycle.variables))
                for rule in sorted(cycle.rules, key=lambda r: r.order):
                    errors[f"{rule.order}.json_logic_trigger"].append(
                        ErrorDetail(
                            msg.format(variables=var_keys), code="cycles-detected"
                        )
                    )
            raise serializers.ValidationError(errors)

        # Form steps are added to the context dictionary in
        # `FormViewSet.logic_rules_bulk_update`. It is a mapping from form step UUID to
        # form step. We rely on it being ordered.
        first_step: FormStep = next(iter(self.context["form_steps"].values()))
        # Note that the order will remain 0, even if a form step was deleted.
        assert first_step.order == 0
        add_missing_steps(graph, first_step)
        new_rule_order = resolve_order(graph)

        # Reorder the incoming data according to the determined order.
        data_new: list[dict[str, object]] = []
        steps: list[list[FormStep]] = []
        for rule in new_rule_order:
            # We can get the original rule data by using the (manually set) pk as an
            # index.
            rule_data = attrs[rule.pk]
            steps.append(list(rule.steps))
            data_new.append(rule_data)

        # Saving it to the context here to avoid determining the steps again when
        # assigning them to the `form_steps` model property. It is an expensive
        # operation, and we can only set a many-to-many relationship after the instances
        # have been created in the database.
        self.context["steps_for_each_rule"] = steps

        return super().validate(data_new)

    def create(self, validated_data):
        rules = super().create(validated_data)
        if not self.context["form"].new_logic_evaluation_enabled:
            return rules

        # Set many-to-many relationship from logic rules to form steps
        for rule, step_list in zip(
            rules, self.context["steps_for_each_rule"], strict=True
        ):
            rule.form_steps.set(step_list)

        return rules


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
