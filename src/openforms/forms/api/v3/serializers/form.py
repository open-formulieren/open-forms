from collections import Counter, defaultdict
from uuid import UUID

from django.db import transaction
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models import Theme
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.service import (
    DuplicateKeyError,
    FormioConfigurationWrapper,
    get_readable_path_from_configuration_path,
)
from openforms.forms.logic_analysis import (  # TODO: use service module for this
    add_missing_steps,
    create_graph,
    detect_cycles,
    resolve_order,
)
from openforms.forms.models import FormLogic
from openforms.prefill.contrib.customer_interactions.constants import (
    PLUGIN_IDENTIFIER as COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
)
from openforms.products.models import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import StrOrPromise
from openforms.variables.constants import FormVariableSources
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.service import get_static_variables

from ....api.serializers.form import (
    FormLiteralsSerializer,
    FormRegistrationBackendSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from ....models import (
    Category,
    Form,
    FormDefinition,
    FormRegistrationBackend,
    FormStep,
    FormVariable,
)
from ..typing import (
    FormLogicRulesData,
    FormStepData,
    FormValidatedData,
    FormVariableData,
)
from .form_step import FormStepSerializer
from .logic_rules import FormLogicListSerializer
from .payment import FormPaymentSerializer
from .variables import FormVariableSerializer


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

    steps = FormStepSerializer(many=True, required=True, source="formstep_set")
    variables = FormVariableSerializer(
        many=True, source="formvariable_set", required=False
    )

    payment = FormPaymentSerializer(required=False, source="*")
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

    registration_backends = FormRegistrationBackendSerializer(many=True, required=False)

    _nested_fields = (
        "confirmation_email_template",
        "formstep_set",
        "formvariable_set",
        "registration_backends",
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
            "registration_backends",
            "variables",
            "payment",
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
        form_definitions_created: dict[UUID, FormDefinition] = {}
        form_steps: list[FormStep] = []
        for index, step_data in enumerate(form_step_data):
            form_definition_data = step_data["form_definition"]
            form_definition, _ = form_definitions.update_or_create(
                uuid=form_definition_data["uuid"],
                defaults={k: v for k, v in form_definition_data.items() if k != "uuid"},
            )
            form_definitions_created[form_definition_data["uuid"]] = form_definition

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

        # These calls are required to create the corresponding component form variables
        # from the form definitions.
        for form_definition in form_definitions_created.values():
            FormVariable.objects.synchronize_for(form_definition)

        registration_backends = validated_data.get("registration_backends", [])
        FormRegistrationBackend.objects.bulk_create(
            FormRegistrationBackend(form=instance, **backend)
            for backend in registration_backends
        )

        form_variables_data = validated_data.get("formvariable_set", [])
        form_variables: list[FormVariable] = []
        for variable_data in form_variables_data:
            form_definition = None
            form_variable_kwargs = {
                k: v for k, v in variable_data.items() if k != "form_definition"
            }

            # See the `.save` method for the `synchronize_for` call.
            if variable_data["source"] == FormVariableSources.component:
                continue

            if form_definition_uuid := variable_data.get("form_definition", None):
                form_definition = form_definitions_created[form_definition_uuid]
                form_variable_kwargs.update(form_definition=form_definition)

            service_fetch_configuration = None
            if service_configuration_data := variable_data.get(
                "service_fetch_configuration"
            ):
                service_fetch_configuration = ServiceFetchConfiguration.objects.create(
                    **service_configuration_data
                )

            form_variable = FormVariable(
                form=instance,
                service_fetch_configuration=service_fetch_configuration,
                **{
                    k: v
                    for k, v in form_variable_kwargs.items()
                    if k != "service_fetch_configuration"
                },
            )
            form_variable.check_data_type_and_initial_value()
            form_variables.append(form_variable)
        FormVariable.objects.bulk_create(form_variables)

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
        form_definitions_created: dict[UUID, FormDefinition] = {}
        for index, step_data in enumerate(form_step_data):
            form_definition_data = step_data["form_definition"]
            form_definition, _ = form_definitions.update_or_create(
                uuid=form_definition_data["uuid"],
                defaults={k: v for k, v in form_definition_data.items() if k != "uuid"},
            )
            form_definitions_created[form_definition.uuid] = form_definition

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
            delete_form_definition = not bool(
                step.form_definition.uuid in form_definitions_created
            )
            step.delete(
                delete_form_definition=delete_form_definition
            )  # Removes the form definition when applicable by calling `.delete`.

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

        # These calls are required to create the corresponding component form variables
        # from the form definitions.
        for form_definition in form_definitions_created.values():
            FormVariable.objects.synchronize_for(form_definition)

        registration_backends = validated_data.get("registration_backends", None)
        if registration_backends is not None:
            instance.registration_backends.all().delete()
            FormRegistrationBackend.objects.bulk_create(
                FormRegistrationBackend(form=instance, **backend)
                for backend in registration_backends
            )

        form_variables_data = validated_data.get("formvariable_set", [])
        form_variables: list[FormVariable] = []
        for variable_data in form_variables_data:
            form_definition = None
            form_variable_kwargs = {
                k: v for k, v in variable_data.items() if k != "form_definition"
            }

            # See the `.save` method for the `synchronize_for` call.
            if variable_data["source"] == FormVariableSources.component:
                continue

            if form_definition_uuid := variable_data.get("form_definition", None):
                form_definition = form_definitions_created[form_definition_uuid]
                form_variable_kwargs.update(form_definition=form_definition)

            service_fetch_configuration = None
            if service_configuration_data := variable_data.get(
                "service_fetch_configuration"
            ):
                service_fetch_configuration = ServiceFetchConfiguration.objects.create(
                    **service_configuration_data
                )

            form_variable = FormVariable(
                form=instance,
                service_fetch_configuration=service_fetch_configuration,
                **{
                    k: v
                    for k, v in form_variable_kwargs.items()
                    if k != "service_fetch_configuration"
                },
            )
            form_variable.check_data_type_and_initial_value()
            form_variables.append(form_variable)
        # Remove the stale variables that were not part of the request.
        instance.formvariable_set.exclude(source=FormVariableSources.component).delete()
        FormVariable.objects.bulk_create(form_variables)

        return instance

    def validate_steps(self, value: list[FormStepData]) -> list[FormStepData]:
        # Step 1: Validate form definitions are unique across all steps.
        unique_fd_uuids = {step["form_definition"]["uuid"] for step in value}
        if len(unique_fd_uuids) < len(value):
            raise serializers.ValidationError(
                _("Non-unique form step - form definition duplicate(s) detected.")
            )

        # Step 2: Validate that the form definitions don't have duplicate component keys.
        configurations: dict[UUID, FormioConfigurationWrapper] = {
            step["form_definition"]["uuid"]: FormioConfigurationWrapper(
                step["form_definition"]["configuration"], validate_unique_keys=True
            )
            for step in value
        }
        # Required for the variable validation.
        self.form_definition_configurations = configurations

        all_keys: list[str] = []
        for form_definition, configuration in configurations.items():
            try:
                for component in configuration:
                    all_keys.append(component["key"])
            except DuplicateKeyError as exc:
                error_message = _(
                    "Duplicate component key detected in form definition {form_definition}."
                ).format(form_definition=form_definition)
                raise ValidationError(error_message) from exc

        # Check the counter to find duplicates.
        errors: list[StrOrPromise] = []
        for component_key, count in Counter(all_keys).items():
            if count < 2:  # no duplicates
                continue

            # Find all the places where it occurs to produce a human readable error
            # message.
            readable_paths: list[str] = []
            for configuration in configurations.values():
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

    def validate_variable_profile_options(
        self,
        index: int,
        variable_data: FormVariableData,
    ) -> None:
        prefill_options = variable_data.get("prefill_options", {})
        if not (
            profile_form_variable_key := prefill_options.get("profile_form_variable")
        ):
            return

        if not (profile_form_definition_uuid := variable_data.get("form_definition")):
            raise ValidationError(
                {
                    f"variables.{index}.key": _(
                        "Profile variable has no form definition specified."
                    )
                }
            )

        profile_config_wrapper = self.form_definition_configurations[
            profile_form_definition_uuid
        ]
        component = profile_config_wrapper[profile_form_variable_key]
        if component["type"] != "customerProfile":
            raise serializers.ValidationError(
                {
                    f"variables.{index}.profileFormVariable": _(
                        "Only variables of 'profile' components are allowed as "
                        "profile form variable."
                    )
                }
            )

    def validate_variable_form_definition(
        self, index: int, attrs: FormVariableData
    ) -> None:
        if not (form_definition_uuid := attrs.get("form_definition")):
            return

        config_wrapper = self.form_definition_configurations.get(form_definition_uuid)
        if not config_wrapper:
            raise ValidationError(
                {
                    f"variables.{index}.form_definition": _(
                        "Unknown form definition specified."
                    )
                }
            )

    def validate_variable_prefill_data(
        self, index: int, attrs: FormVariableData
    ) -> None:
        prefill_plugin = attrs.get("prefill_plugin") or ""
        prefill_attribute = attrs.get("prefill_attribute") or ""
        prefill_options = attrs.get("prefill_options")

        if prefill_plugin and prefill_options and prefill_attribute:
            raise ValidationError(
                {
                    f"variables.{index}.nonFieldErrors": _(
                        "Prefill plugin, attribute and options can not be specified at the same time."
                    ),
                }
            )

        if (prefill_plugin and not (prefill_attribute or prefill_options)) or (
            not prefill_plugin and (prefill_attribute or prefill_options)
        ):
            raise ValidationError(
                {
                    f"variables.{index}.nonFieldErrors": _(
                        "Prefill plugin must be specified with either prefill attribute or prefill options."
                    )
                }
            )

    def validate_variable_data(self, attrs: FormValidatedData) -> None:
        static_keys = [item.key for item in get_static_variables()]
        component_keys = [
            component["key"]
            for configuration in self.form_definition_configurations.values()
            for component in configuration
        ]
        existing_profile_form_vars: list[str] = []

        for index, variable_data in enumerate(attrs.get("formvariable_set", [])):
            # To have a smooth transition in the front-end from v2 to v3, only user-defined
            # variables will be processed/saved from the request. Component variable
            # are automagically created/updated when the form gets saved.
            if variable_data["source"] == FormVariableSources.component:
                continue

            if variable_data["key"] in static_keys:
                raise ValidationError(
                    {
                        f"variables.{index}.key": [
                            (
                                "The variable key cannot be equal to any of the "
                                "following static variable keys: {static_keys}."
                            ).format(static_keys=", ".join(static_keys)),
                        ]
                    },
                    code="unique",
                )
            elif variable_data["key"] in component_keys:
                raise ValidationError(
                    {
                        f"variables.{index}.key": [
                            (
                                "The variable key cannot be equal to any of the "
                                "following component variable keys: {component_keys}."
                            ).format(component_keys=", ".join(component_keys)),
                        ]
                    },
                    code="unique",
                )

            self.validate_variable_prefill_data(index, variable_data)
            self.validate_variable_form_definition(index, variable_data)
            self.validate_variable_profile_options(index, variable_data)

            prefill_plugin = variable_data.get("prefill_plugin")
            prefill_options = variable_data.get("prefill_options", {})
            profile_form_variable = prefill_options.get("profile_form_variable")

            if prefill_plugin != COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER or any(
                (not prefill_options, not profile_form_variable)
            ):
                continue

            assert profile_form_variable, "No profile variable!"
            if profile_form_variable in existing_profile_form_vars:
                raise ValidationError(
                    {
                        f"variables.{index}.prefillOptions.profileFormVariable": _(
                            "This profile form variable is already used in another "
                            "communication preferences prefill plugin."
                        )
                    },
                    code="unique",
                )

            existing_profile_form_vars.append(profile_form_variable)

    def validate(self, attrs: FormValidatedData) -> FormValidatedData:
        # validate is called multiple times because of the nested serializer fields.
        # For example ModelTranslationsSerializer is calling it 2 times (current amount
        # of languages) but at this point the attrs contain only the related data (child).
        # Fixing/updating ModelTranslationsSerializer can be tricky (it's used a lot in
        # the project), so that's why we do the check here.
        steps = attrs.get("formstep_set")
        if steps is None:
            return attrs

        is_appointment = attrs.get("is_appointment")

        # regular form should have at least one step
        if not is_appointment and len(steps) == 0:
            raise serializers.ValidationError(
                _("At least one form step is required in a regular form.")
            )

        # appointment form should not have any steps
        if is_appointment and len(steps) > 0:
            raise serializers.ValidationError(
                _("Form steps are not allowed in an appointment form.")
            )

        # validate variables after validation of the form definitions were ran
        self.validate_variable_data(attrs)

        form_step_data = attrs.get("formstep_set", [])
        logic_rule_data = attrs.get("formlogic_set", [])
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

            attrs["formlogic_set"] = self._validate_form_logic(
                logic_rule_data,
                form_steps,
                attrs.get("new_logic_evaluation_enabled", False),
            )

        return attrs

    def save(self, **kwargs):
        instance = super().save(**kwargs, uuid=self.context["form_uuid"])
        return instance
