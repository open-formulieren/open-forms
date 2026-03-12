from collections import Counter, defaultdict

from django.db import transaction
from django.utils.text import get_text_list
from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models import Theme
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.service import get_readable_path_from_configuration_path
from openforms.forms.logic_analysis import (  # TODO: use service module for this
    add_missing_steps,
    create_graph,
    detect_cycles,
    resolve_order,
)
from openforms.forms.models import FormLogic
from openforms.products.models import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import StrOrPromise

from ....api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from ....models import Category, Form, FormDefinition, FormStep, FormVariable
from ..typing import FormLogicRulesData, FormStepData, FormValidatedData
from .form_step import FormStepSerializer
from .logic_rules import FormLogicListSerializer


@extend_schema_serializer(component_name="FormV3Serializer")
class FormSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(
        required=False,
        allow_null=True,
        queryset=Product.objects.all(),
        slug_field="uuid",
    )
    category = serializers.SlugRelatedField(
        required=False,
        allow_null=True,
        queryset=Category.objects.all(),
        slug_field="uuid",
    )
    theme = serializers.SlugRelatedField(
        required=False,
        allow_null=True,
        queryset=Theme.objects.all(),
        slug_field="uuid",
    )

    steps = FormStepSerializer(many=True, source="formstep_set")
    logic_rules = FormLogicListSerializer(required=False, source="formlogic_set")

    appointment_options = AppointmentOptionsSerializer(
        source="*",
        required=False,
        allow_null=True,
    )

    literals = FormLiteralsSerializer(source="*", required=False)

    confirmation_email_template = ConfirmationEmailTemplateSerializer(
        required=False, allow_null=True
    )

    is_deleted = serializers.BooleanField(source="_is_deleted", required=False)
    submissions_removal_options = SubmissionsRemovalOptionsSerializer(
        source="*", required=False
    )

    translations = ModelTranslationsSerializer()

    _nested_fields = (
        "confirmation_email_template",
        "formstep_set",
        "formlogic_set",
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "internal_remarks",
            "login_required",
            "translation_enabled",
            "appointment_options",
            "literals",
            "product",
            "slug",
            "category",
            "theme",
            "steps",
            "logic_rules",
            "show_progress_indicator",
            "show_summary_progress",
            "maintenance_mode",
            "active",
            "activate_on",
            "deactivate_on",
            "is_deleted",
            "submission_confirmation_template",
            "introduction_page_content",
            "explanation_template",
            "submission_allowed",
            "submission_limit",
            "submission_counter",
            "suspension_allowed",
            "ask_privacy_consent",
            "ask_statement_of_truth",
            "submissions_removal_options",
            "confirmation_email_template",
            "send_confirmation_email",
            "display_main_website_link",
            "include_confirmation_page_content_in_pdf",
            "translations",
            "new_renderer_enabled",
            "new_logic_evaluation_enabled",
        )
        extra_kwargs = {
            "uuid": {  # retrieved from the context passed through from the view
                "read_only": True,
            },
        }

    def _validate_form_logic(
        self,
        value: list[FormLogicRulesData],
        form_steps: list[FormStep],
        new_logic_evaluation_enabled: bool,
    ) -> list[FormLogicRulesData]:
        if not new_logic_evaluation_enabled:
            return value

        # This will only run when the logic rules have passed individual serializer
        # validation, so we can initialize model instances here.
        # Note: model instances without a pk are not hashable, which is a requirement to
        # use them in the graph, so we assign it manually. These rules will just live in
        # memory, so it will not result in conflicts with existing rules.
        _temporary_rules: list[FormLogic] = []
        for index, rule_data in enumerate(value):
            rule = FormLogic(
                **{k: v for k, v in rule_data.items() if k != "form_steps"}, pk=index
            )
            rule.form = self.instance  # TODO: use mock form here

            _temporary_rules.append(rule)

        # TODO: figure out how to handle this without form instances
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
        first_step: FormStep = next(iter(form_steps))
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
            rule_data = value[rule.pk]
            steps.append(list(rule.steps))
            data_new.append(rule_data)

        field: FormLogicListSerializer = self.fields["logic_rules"]  # pyright: ignore[reportAssignmentType]
        return field.validate(data_new)

    def validate(self, attrs: FormValidatedData) -> FormValidatedData:
        validated_data = super().validate(attrs)

        form_step_data = validated_data.get("formstep_set", [])
        logic_rule_data = validated_data.get("formlogic_set", [])
        if form_step_data and logic_rule_data:
            # TODO: check if empty form steps are allowed to be given for logic rules
            form_steps = [
                FormStep(order=index, slug=data.get("slug"))
                for index, data in enumerate(form_step_data)
            ]

            for rule in logic_rule_data:
                if rule_form_steps := rule.get("form_steps"):
                    unknown_form_steps = set(rule_form_steps) - set(
                        step.slug for step in form_steps
                    )

                    if unknown_form_steps:
                        raise serializers.ValidationError(
                            {
                                "logic_rules": _(
                                    "Rule {order} has unknown form steps: {steps}"
                                ).format(
                                    order=rule["order"],
                                    steps=",".join(unknown_form_steps),
                                )
                            }
                        )

            validated_data["formlogic_set"] = self._validate_form_logic(
                logic_rule_data,
                form_steps,
                validated_data.get("new_logic_evaluation_enabled", False),
            )
        return validated_data

    @transaction.atomic()
    def create(self, validated_data: FormValidatedData) -> Form:
        instance = super().create(
            {k: v for k, v in validated_data.items() if k not in self._nested_fields}
        )
        logic_rules = validated_data.get("formlogic_set", [])

        confirmation_email_template = validated_data.get("confirmation_email_template")
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )

        form_step_data = validated_data["formstep_set"]
        # fmt:off
        form_definitions = (
            FormDefinition.objects
            .select_for_update(nowait=True)
            .filter(uuid__in=(step_data["form_definition"]["uuid"] for step_data in form_step_data))
        )
        # fmt:on
        len(form_definitions)  # Evaluate the queryset to acquire the locks.
        form_steps: list[FormStep] = []
        for index, step_data in enumerate(form_step_data):
            form_definition_data = step_data["form_definition"]
            form_definition, _ = form_definitions.update_or_create(
                uuid=form_definition_data["uuid"],
                defaults={k: v for k, v in form_definition_data.items() if k != "uuid"},
            )

            form_steps.append(
                FormStep(
                    **{
                        **step_data,
                        "form_definition": form_definition,
                        "form": instance,
                        "order": index,
                    }
                )
            )

        form_steps = FormStep.objects.bulk_create(form_steps)
        if instance.new_logic_evaluation_enabled:
            for rule_data in logic_rules:
                rule = FormLogic.objects.create(**rule_data, form=instance)
                rule.form_steps.set(
                    [
                        form_step
                        for form_step in form_steps
                        if form_step.slug in rule_data["form_steps"]
                    ]
                )

        return instance

    @transaction.atomic()
    def update(self, instance: Form, validated_data: FormValidatedData) -> Form:
        instance = super().update(
            instance,
            {k: v for k, v in validated_data.items() if k not in self._nested_fields},
        )

        confirmation_email_template = validated_data.get(
            "confirmation_email_template", None
        )
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )

        assigned_steps: list[FormStep] = []
        form_step_data = validated_data["formstep_set"]
        # fmt:off
        form_definitions = (
            FormDefinition.objects
            .select_for_update(nowait=True)
            .filter(uuid__in=(step_data["form_definition"]["uuid"] for step_data in form_step_data))
        )
        # fmt:on
        len(form_definitions)  # Evaluate the queryset to acquire the locks.
        for index, step_data in enumerate(form_step_data):
            form_definition_data = step_data["form_definition"]
            form_definition, _ = form_definitions.update_or_create(
                uuid=form_definition_data["uuid"],
                defaults={k: v for k, v in form_definition_data.items() if k != "uuid"},
            )

            step = FormStep(  # TODO: use update_or_create (nice to have)
                **{**step_data, "form_definition": form_definition},
                order=index,
                form=instance,
            )
            assigned_steps.append(step)

        steps_to_delete = instance.formstep_set.exclude(
            pk__in=(step.pk for step in assigned_steps)
        )
        for step in steps_to_delete:
            step.delete()  # Removes the form definition when applicable by calling `.delete`.

        # Generate form steps after deleting existings steps, to allow correct calculation of
        # the `order` field.
        form_steps: list[FormStep] = sorted(assigned_steps, key=lambda step: step.order)
        for step in form_steps:
            step.save()

        logic_rules = validated_data.get("formlogic_set", [])
        if instance.new_logic_evaluation_enabled:
            logic_rules_ids: list[int] = []
            for rule_data in logic_rules:
                rule = FormLogic.objects.create(**rule_data, form=instance)
                rule.form_steps.set(
                    [
                        form_step
                        for form_step in form_steps
                        if form_step.slug in rule_data["form_steps"]
                    ]
                )
                logic_rules_ids.append(rule.pk)

            # Remove existing logic rules from the form.
            # fmt:off
            (
                FormLogic.objects
                .exclude(id__in=logic_rules_ids)
                .filter(form=instance)
                .delete()
            )
            # fmt:on

        return instance

    def validate_steps(self, value: list[FormStepData]) -> list[FormStepData]:
        if not value:
            return value

        # Step 1: Validate form definitions are unique across all steps.
        unique_fd_uuids = {step["form_definition"]["uuid"] for step in value}
        if len(unique_fd_uuids) < len(value):
            raise serializers.ValidationError(
                _("Non-unique form step - form definition duplicate(s) detected.")
            )

        # Step 2: Validate that the form definitions don't have duplicate component keys.
        configurations = [
            FormioConfigurationWrapper(step["form_definition"]["configuration"])
            for step in value
        ]
        # Use component keys from original data to detect duplicates inside
        # a single form definition. The FormioConfigurationWrapper's `component_keys`
        # filters out the duplicates already so we can't use that for this purpose.
        all_keys = [
            component["key"]
            for configuration in configurations
            for component in configuration.configuration["components"]
        ]

        # check the counter to find duplicates
        errors: list[StrOrPromise] = []
        for component_key, count in Counter(all_keys).items():
            if count < 2:  # no duplicates
                continue

            # find all the places where it occurs to produce a human readable error
            # message
            readable_paths: list[str] = []
            for configuration in configurations:
                if component_key not in configuration:
                    continue

                paths = [
                    path
                    for path, component in configuration.flattened_by_path.items()
                    if component["key"] == component_key
                ]

                for path in paths:
                    readable_path = get_readable_path_from_configuration_path(
                        configuration.configuration, path
                    )
                    readable_paths.append(readable_path)

            error_message = _('"{duplicate_key}" (in {paths})').format(
                duplicate_key=component_key, paths=", ".join(readable_paths)
            )
            errors.append(error_message)

        if errors:
            raise serializers.ValidationError(
                _("Detected duplicate keys in configuration: {errors}").format(
                    errors=get_text_list(errors, ", ")
                )
            )

        return value

    @transaction.atomic()
    def save(self, **kwargs):
        instance = super().save(**kwargs, uuid=self.context["form_uuid"])

        for step in instance.formstep_set.all():
            # call this synchronously so that it's part of the same DB transaction.
            FormVariable.objects.synchronize_for(step.form_definition)

        return instance
