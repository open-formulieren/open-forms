from collections import defaultdict
from collections.abc import Collection

from django.utils.translation import gettext_lazy as _

from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from openforms.api.fields import RelatedFieldFromContext
from openforms.api.serializers import ListWithChildSerializer

from ....constants import FormTypeChoices
from ....logic_analysis import (
    CyclesDetected,
    analyze_rules,
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
        form: Form = self.context["form"]
        if (is_appointment := form.type == FormTypeChoices.appointment) and attrs:
            raise serializers.ValidationError(
                _("Appointment forms cannot have logic rules.")
            )
        if is_appointment or not form.form_step_map:
            return super().validate(attrs)

        # This will only run when the logic rules have passed individual serializer
        # validation, so we can initialize model instances here.
        rules_to_index_mapping: dict[FormLogic, int] = {
            # Note: model instances without a pk are not hashable, which is a
            # requirement to use them in the analysis graph, so we assign it manually.
            # These rules will just live in memory, so it will not result in conflicts
            # with existing rules.
            FormLogic(**rule_data, pk=-i): i
            for i, rule_data in enumerate(attrs)
        }

        first_step: FormStep = min(
            form.form_step_map.values(), key=lambda step: step.order
        )
        try:
            updated_rules_and_steps = analyze_rules(
                self.context["form"],
                rules=list(rules_to_index_mapping.keys()),
                first_step=first_step,
            )
        except CyclesDetected as exc:
            msg = _("Rule contains cycles through variable(s): {variables}.")
            errors: defaultdict[str, list[ErrorDetail]] = defaultdict(list)
            for cycle in exc.cycles:
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

        # Reorder the incoming data according to the determined order.
        steps: list[Collection[FormStep]] = []
        reordered_rule_data: list[dict[str, object]] = []

        for rule, rule_steps in updated_rules_and_steps:
            # Lookup the original rule data by checking our rule-to-index map created
            # earlier.
            rule_data_index = rules_to_index_mapping[rule]
            reordered_rule_data.append(attrs[rule_data_index])
            steps.append(rule_steps)

        self.context["steps_for_each_rule"] = steps
        return super().validate(reordered_rule_data)

    def create(self, validated_data):
        rules = super().create(validated_data)
        form: Form = self.context["form"]
        if form.type == FormTypeChoices.appointment or not form.form_step_map:
            return rules

        # the (auto-created) through model
        FormLogicFormSteps = FormLogic._meta.get_field(
            "form_steps"
        ).remote_field.through

        # drop the old relations and create the expected ones.
        expected_relations = [
            FormLogicFormSteps(formlogic=rule, formstep=step)
            for rule, steps in zip(
                rules, self.context["steps_for_each_rule"], strict=True
            )
            for step in steps
        ]
        FormLogicFormSteps.objects.filter(formlogic__form=self.context["form"]).delete()
        FormLogicFormSteps.objects.bulk_create(expected_relations)

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
    form_steps = NestedHyperlinkedRelatedField(
        read_only=True,
        many=True,
        view_name="api:form-steps-detail",
        lookup_field="uuid",
        parent_lookup_kwargs={"form_uuid_or_slug": "form__uuid"},
        label=_("form steps"),
        help_text=_(
            "Form steps on which the rule will be executed, determined by logic rule "
            "analysis."
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
