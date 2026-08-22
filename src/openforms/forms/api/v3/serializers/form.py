import itertools
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, MutableMapping, Sequence
from typing import TypedDict
from uuid import UUID

from django.db import transaction
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError

from formio_types import AnyComponent, CustomerProfile
from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models import Theme
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.formio.service import FormioConfig, get_branch_representation
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
    HelpCalloutPageSerializer,
    HelpDialogSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from ....constants import FormTypeChoices
from ....logic_analysis import CyclesDetected, analyze_rules
from ....models import (
    Category,
    Form,
    FormDefinition,
    FormLogic,
    FormRegistrationBackend,
    FormStep,
    FormVariable,
)
from ...validators import RequireAppointmentsPlugin
from ..typing import (
    FormLogicActionData,
    FormLogicData,
    FormStepData,
    FormValidatedData,
    FormVariableData,
)
from ..validation import ActionsErrors, validate_logic_actions
from .form_step import FormStepSerializer
from .logic_rules import FormLogicSerializer
from .payment import FormPaymentSerializer
from .variables import FormVariableSerializer


class RuleErrors(TypedDict):
    """
    Validation errors for a single logic rule.
    """

    actions: ActionsErrors


type RulesErrors = MutableMapping[int, RuleErrors]
"""
Mapping of rule errors for the collection of rules, keyed by rule index.
"""


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
    logic_rules = FormLogicSerializer(many=True, required=False, source="formlogic_set")

    payment = FormPaymentSerializer(required=False, source="*")

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

    help_callout_page = HelpCalloutPageSerializer(
        source="*", required=False, allow_null=True
    )

    _nested_fields = (
        "confirmation_email_template",
        "formstep_set",
        "formvariable_set",
        "formlogic_set",
        "registration_backends",
    )

    help_dialog = HelpDialogSerializer(
        source="*",
        required=False,
        allow_null=False,
        label=_("Help dialog configuration"),
        help_text=_(
            "When the nested content field is not empty, the SDK should render help "
            "controls to assist the user filling out the form."
        ),
    )

    formio_configs: list[FormioConfig] | None = None

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
            "type",
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
            "help_callout_page",
            "help_dialog",
        )
        extra_kwargs = {
            "uuid": {  # retrieved from the context passed through from the view
                "read_only": True,
            },
            "type": {"validators": [RequireAppointmentsPlugin()]},
        }

    def _validate_actions(self, form: Form, temp_rules: Mapping[FormLogic, int]):
        form_variables = {
            var.key: var for var in FormVariable.objects.filter(form=form)
        }
        form_step_slugs = set(form.formstep_set.values_list("slug", flat=True))
        rule_errors: RulesErrors = {}

        _formio_config: FormioConfig | None = None

        def _find_component(key: str) -> AnyComponent | None:
            """
            Find the component with key ``key`` in any of the form steps.
            """
            nonlocal _formio_config

            if _formio_config is None:
                queryset = form.formstep_set.select_related("form_definition")
                all_components = list(
                    itertools.chain.from_iterable(
                        form_step.form_definition.configuration["components"]
                        for form_step in queryset
                    )
                )
                _formio_config = FormioConfig(
                    name="<validation>", components=all_components
                )

            if key in _formio_config:
                return _formio_config[key]

            return None

        for index, rule in enumerate(temp_rules):
            # at this point, the shape of the actions has been validated, but their semantic
            # meaning hasn't yet
            actions: Sequence[FormLogicActionData] = rule.actions
            if rule_action_errors := validate_logic_actions(
                actions,
                find_component=_find_component,
                form_variables=form_variables,
                form_step_slugs=form_step_slugs,
            ):
                rule_errors[index] = {"actions": rule_action_errors}

        if rule_errors:
            raise ValidationError({"logic_rules": rule_errors})  # pyright:ignore[reportArgumentType]

    def _validate_and_process_logic_rules(
        self,
        form: Form,
        logic_rules_raw: list[FormLogicData],
        temp_logic_rules: dict[FormLogic, int],
    ):
        first_step: FormStep | None = min(
            form.form_step_map.values(), key=lambda step: step.order, default=None
        )

        try:
            updated_rules_and_steps = analyze_rules(
                form,
                rules=list(temp_logic_rules.keys()),
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
        reordered_rule_data: list[FormLogicData] = []
        for rule, rule_steps in updated_rules_and_steps:
            # Lookup the original rule data by checking our rule-to-index map created
            # earlier.
            rule_data_index = temp_logic_rules[rule]
            reordered_rule_data.append(logic_rules_raw[rule_data_index])
            steps.append(rule_steps)

        self.context["steps_for_each_rule"] = steps
        return reordered_rule_data

    @transaction.atomic()
    def create(self, validated_data: FormValidatedData) -> Form:
        instance = super().create(
            {k: v for k, v in validated_data.items() if k not in self._nested_fields}
        )

        # 1. confirmation email template
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

        # 2. form definitions/steps
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

        # These calls are required to create the corresponding component form variables
        # from the form definitions.
        for form_definition in form_definitions_created.values():
            FormVariable.objects.synchronize_for(form_definition)

        # 3. registration backends
        registration_backends = validated_data.get("registration_backends", [])
        FormRegistrationBackend.objects.bulk_create(
            FormRegistrationBackend(form=instance, **backend)
            for backend in registration_backends
        )

        #  4. form variables
        form_variables_data = validated_data.get("formvariable_set", [])
        form_variables: list[FormVariable] = []
        for variable_data in form_variables_data:
            service_fetch_configuration = None
            if service_configuration_data := variable_data.pop(
                "service_fetch_configuration", None
            ):
                service_fetch_configuration_id = service_configuration_data.pop(
                    "id", None
                )
                service_fetch_configuration, __ = (
                    ServiceFetchConfiguration.objects.update_or_create(
                        id=service_fetch_configuration_id,
                        defaults=service_configuration_data,
                    )
                )

            variable_kwargs = dict(variable_data)
            form_variable = FormVariable(
                form=instance,
                service_fetch_configuration=service_fetch_configuration,
                **variable_kwargs,
            )
            form_variable.check_data_type_and_initial_value()
            form_variables.append(form_variable)
        FormVariable.objects.bulk_create(form_variables)

        # 5. logic rules
        logic_rules_raw: list[FormLogicData] = validated_data.get("formlogic_set", [])

        if not logic_rules_raw:
            return instance

        # Note: model instances without a pk are not hashable, which is a requirement to
        # use them in the analysis graph, so we assign it manually. These rules will just
        # live in memory and they will be saved below, after they are analyzed.
        temp_rules_instances: dict[FormLogic, int] = {
            FormLogic(**logic_rule_data, pk=-index, form=instance): index
            for index, logic_rule_data in enumerate(logic_rules_raw)
        }

        # We have to do these steps in the create method instead of the ideal/proper
        # choice to do that inside the validate method. The form instance is important
        # to have been created at the time that we do these validations, as the related
        # nested fields are needed (have to be saved and available to access). Adding
        # that to the validate method would require a huge refactor as a lot of our
        # current implementation depends on the (saved) form instance.
        self._validate_actions(instance, temp_rules_instances)
        reordered_rules = self._validate_and_process_logic_rules(
            instance, logic_rules_raw, temp_rules_instances
        )

        # Save the form logic rules in the correct/updated order
        FormLogic.objects.bulk_create(
            [FormLogic(**rule, form=instance) for rule in reordered_rules]
        )

        return instance

    @transaction.atomic()
    def update(self, instance: Form, validated_data: FormValidatedData) -> Form:
        instance = super().update(
            instance,
            {k: v for k, v in validated_data.items() if k not in self._nested_fields},
        )

        # 1. confirmation email template
        confirmation_email_template = validated_data.get(
            "confirmation_email_template", None
        )
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )

        # 2. form definitions/steps
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

        # Remove the form steps that are not part of the request along with their
        # form definitions when applicable.
        steps_to_delete = instance.formstep_set.exclude(
            pk__in=(step.pk for step in assigned_steps)
        )
        form_definitions_to_delete = [
            step.form_definition.pk
            for step in steps_to_delete
            if not step.form_definition.is_reusable
            and step.form_definition.uuid not in form_definitions_created
        ]
        # Use query manager delete methods to bypass model defined `delete` methods.
        steps_to_delete.delete()
        FormDefinition.objects.filter(pk__in=form_definitions_to_delete).delete()

        # Generate form steps after deleting existings steps, to allow correct calculation of
        # the `order` field.
        for step in sorted(assigned_steps, key=lambda step: step.order):
            step.save()

        # These calls are required to create the corresponding component form variables
        # from the form definitions.
        for form_definition in form_definitions_created.values():
            FormVariable.objects.synchronize_for(form_definition)

        # 3. registration backends
        registration_backends = validated_data.get("registration_backends", None)
        if registration_backends is not None:
            instance.registration_backends.all().delete()
            FormRegistrationBackend.objects.bulk_create(
                FormRegistrationBackend(form=instance, **backend)
                for backend in registration_backends
            )

        # 4. form variables
        form_variables_data = validated_data.get("formvariable_set", [])
        form_variables: list[FormVariable] = []
        for variable_data in form_variables_data:
            service_fetch_configuration = None
            if service_configuration_data := variable_data.pop(
                "service_fetch_configuration", None
            ):
                service_fetch_configuration_id = service_configuration_data.pop(
                    "id", None
                )
                service_fetch_configuration, __ = (
                    ServiceFetchConfiguration.objects.update_or_create(
                        id=service_fetch_configuration_id,
                        defaults=service_configuration_data,
                    )
                )

            variable_kwargs = dict(variable_data)
            form_variable = FormVariable(
                form=instance,
                service_fetch_configuration=service_fetch_configuration,
                **variable_kwargs,
            )
            form_variable.check_data_type_and_initial_value()
            form_variables.append(form_variable)
        # Remove the stale variables that were not part of the request.
        instance.formvariable_set.exclude(source=FormVariableSources.component).delete()
        FormVariable.objects.bulk_create(form_variables)

        # 5. logic rules
        logic_rules_raw = validated_data.get("formlogic_set", [])
        if not logic_rules_raw:
            return instance

        # Note: model instances without a pk are not hashable, which is a requirement to
        # use them in the analysis graph, so we assign it manually. These rules will just
        # live in memory and they will be saved below, after they are analyzed.
        temp_rules_instances: dict[FormLogic, int] = {
            FormLogic(**logic_rule_data, pk=-index, form=instance): index
            for index, logic_rule_data in enumerate(logic_rules_raw)
        }

        # We have to do these steps in the create method instead of the ideal/proper
        # choice to do that inside the validate method. The form instance is important
        # to have been created at the time that we do these validations, as the related
        # nested fields are needed (have to be saved and available to access). Adding
        # that to the validate method would require a huge refactor as a lot of our
        # current implementation depends on the (saved) form instance.
        self._validate_actions(instance, temp_rules_instances)
        reordered_rules = self._validate_and_process_logic_rules(
            instance, logic_rules_raw, temp_rules_instances
        )

        # Remove the existing logic rules.
        instance.formlogic_set.all().delete()
        # Save the form logic rules in the correct/updated order.
        FormLogic.objects.bulk_create(
            [FormLogic(**rule, form=instance) for rule in reordered_rules]
        )

        return instance

    def validate_steps(self, value: list[FormStepData]) -> list[FormStepData]:
        # Step 1: Validate form definitions are unique across all steps.
        unique_fd_uuids = {step["form_definition"]["uuid"] for step in value}
        if len(unique_fd_uuids) < len(value):
            raise serializers.ValidationError(
                _("Non-unique form step - form definition duplicate(s) detected.")
            )

        # Step 2: Validate that the form definitions don't have duplicate component
        # keys across steps. The individual step configurations have been validated
        # for uniqueness already.
        formio_configs: list[FormioConfig] = []
        # deliberately loop over each step and its components so that duplicates get
        # added multiple times and we can find all occurrences in all steps
        all_keys: list[str] = []
        for step in value:
            components = step["form_definition"]["configuration"].get("components", [])
            formio_config = FormioConfig(name="<validation>", components=components)
            formio_configs.append(formio_config)
            for component in formio_config:
                all_keys.append(component.key)

        # Required for the variable validation later on.
        self.formio_configs = formio_configs

        # Check the counter to find duplicates.
        errors: list[StrOrPromise] = []
        for component_key, count in Counter(all_keys).items():
            if count < 2:  # no duplicates
                continue

            # Find all the places where it occurs to produce a human readable error
            # message.
            readable_paths: list[str] = []
            for formio_config in formio_configs:
                if component_key not in formio_config:
                    continue
                branch = formio_config.get_parents(
                    component_key,
                    ignore_editgrid_prefix=True,
                    add_self=True,
                )
                readable_path = get_branch_representation(branch)
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
        errors: dict[str, list[ErrorDetail]],
        existing_profile_form_vars: list[str],
    ) -> None:
        prefill_options = variable_data.get("prefill_options", {})
        if not (
            profile_form_variable_key := prefill_options.get("profile_form_variable")
        ):
            return

        component: AnyComponent | None = None
        assert self.formio_configs is not None, (
            "Must be set during earlier step validation"
        )
        for formio_config in self.formio_configs:
            if profile_form_variable_key not in formio_config:
                continue
            component = formio_config[profile_form_variable_key]
            break
        else:
            error_message = ErrorDetail(
                f"Unknown component key '{profile_form_variable_key}' specified for profile form variable",
                code="invalid",
            )
            errors[f"variables.{index}"].append(error_message)

        if component and not isinstance(component, CustomerProfile):
            error_message = ErrorDetail(
                _(  # pyright: ignore[reportArgumentType]
                    "Only variables of 'profile' components are allowed as "
                    "profile form variable."
                ),
                code="invalid",
            )
            errors[f"variables.{index}"].append(error_message)

        prefill_plugin = variable_data.get("prefill_plugin")
        if prefill_plugin == COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER or any(
            (prefill_options, profile_form_variable_key)
        ):
            if profile_form_variable_key:
                if profile_form_variable_key in existing_profile_form_vars:
                    error_message = ErrorDetail(
                        _(  # pyright: ignore[reportArgumentType]
                            "This profile form variable is already used in another "
                            "communication preferences prefill plugin."
                        ),
                        code="unique",
                    )
                    errors[f"variables.{index}"].append(error_message)

                existing_profile_form_vars.append(profile_form_variable_key)

    def validate_variable_prefill_data(
        self, index: int, attrs: FormVariableData, errors: dict[str, list[ErrorDetail]]
    ) -> None:
        prefill_plugin = attrs.get("prefill_plugin") or ""
        prefill_attribute = attrs.get("prefill_attribute") or ""
        prefill_options = attrs.get("prefill_options")

        if prefill_plugin and prefill_options and prefill_attribute:
            error_message = ErrorDetail(
                _(  # pyright: ignore[reportArgumentType]
                    "Prefill plugin, attribute and options can not be specified at the same time."
                ),
                code="invalid",
            )
            errors[f"variables.{index}"].append(error_message)

        if (prefill_plugin and not (prefill_attribute or prefill_options)) or (
            not prefill_plugin and (prefill_attribute or prefill_options)
        ):
            error_message = ErrorDetail(
                _(  # pyright: ignore[reportArgumentType]
                    "Prefill plugin must be specified with either prefill attribute or prefill options."
                ),
                code="invalid",
            )
            errors[f"variables.{index}"].append(error_message)

    def validate_variable_data(self, attrs: FormValidatedData) -> None:
        if not (variables_data := attrs.get("formvariable_set", [])):
            return

        static_keys = [item.key for item in get_static_variables()]
        assert self.formio_configs is not None, (
            "Must be set during earlier step validation"
        )
        component_keys = [
            component.key
            for formio_config in self.formio_configs
            for component in formio_config
        ]
        existing_profile_form_vars: list[str] = []
        errors: dict[str, list[ErrorDetail]] = defaultdict(list)
        variables: list[FormVariableData] = []
        for index, variable_data in enumerate(variables_data):
            # To have a smooth transition in the front-end from v2 to v3, only user-defined
            # variables will be processed/saved from the request. Component variable
            # are automagically created/updated when the form gets saved.
            if variable_data["source"] == FormVariableSources.component:
                continue

            if variable_data["key"] in static_keys:
                error_message = ErrorDetail(
                    (
                        "The variable key cannot be equal to any of the "
                        "following static variable keys: {static_keys}."
                    ).format(static_keys=", ".join(static_keys)),
                    code="unique",
                )
                errors[f"variables.{index}"].append(error_message)
            elif variable_data["key"] in component_keys:
                error_message = ErrorDetail(
                    (
                        "The variable key cannot be equal to any of the "
                        "following component variable keys: {component_keys}."
                    ).format(component_keys=", ".join(component_keys)),
                    code="unique",
                )
                errors[f"variables.{index}"].append(error_message)

            self.validate_variable_prefill_data(index, variable_data, errors)
            self.validate_variable_profile_options(
                index, variable_data, errors, existing_profile_form_vars
            )

            variables.append(variable_data)

        if errors:
            raise ValidationError(errors)

        attrs["formvariable_set"] = variables

    def validate_amount_of_steps(self, attrs: FormValidatedData) -> None:
        # validate is called multiple times because of the nested serializer fields.
        # For example ModelTranslationsSerializer is calling it 2 times (current amount
        # of languages) but at this point the attrs contain only the related data (child).
        # Fixing/updating ModelTranslationsSerializer can be tricky (it's used a lot in
        # the project), so that's why we do the check here.
        steps = attrs.get("formstep_set")
        form_type = attrs.get("type")
        if steps is None and form_type is None:
            return

        num_steps = len(steps)
        match form_type:
            # regular form should have at least one step
            case FormTypeChoices.regular if num_steps == 0:
                raise serializers.ValidationError(
                    _("At least one form step is required in a regular form.")
                )
            # appointment form should not have any steps
            case FormTypeChoices.appointment if num_steps > 0:
                raise serializers.ValidationError(
                    _("Form steps are not allowed in an appointment form.")
                )
            # single step form should have exactly one step
            case FormTypeChoices.single_step if num_steps != 1:
                raise serializers.ValidationError(
                    _("Exactly one form step is required in a single step form.")
                )

    def validate(self, attrs: FormValidatedData) -> FormValidatedData:
        self.validate_amount_of_steps(attrs)

        # validate variables after validation of the form definitions were ran
        self.validate_variable_data(attrs)
        return attrs

    def save(self, **kwargs):
        instance = super().save(**kwargs, uuid=self.context["form_uuid"])
        return instance
