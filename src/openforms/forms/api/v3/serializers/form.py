from typing import Any, cast  # noqa: TID251
from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models.theme import Theme
from openforms.formio.utils import iter_components
from openforms.products.models.product import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer
from openforms.typing import JSONValue

from ....api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from ....models.category import Category
from ....models.form import Form
from ....models.form_definition import FormDefinition
from ....models.form_step import FormStep
from ....models.form_variable import FormVariable
from ....sanitizer import sanitize_component
from ....validators import (
    FakeFormDefinition,
    validate_no_duplicate_keys_across_steps,
)
from .form_step import FormStepData, FormStepSerializer


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

    steps = FormStepSerializer(many=True, source="formstep_set", required=False)

    appointment_options = AppointmentOptionsSerializer(
        source="*",
        required=False,
        allow_null=True,
    )

    literals = FormLiteralsSerializer(source="*", required=False)

    is_deleted = serializers.BooleanField(source="_is_deleted", required=False)
    submissions_removal_options = SubmissionsRemovalOptionsSerializer(
        source="*", required=False
    )

    translations = ModelTranslationsSerializer()

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

    @transaction.atomic()
    def create(self, validated_data: dict[str, Any]) -> Form:
        form_step_data = validated_data.pop("formstep_set", [])

        instance = super().create(validated_data)

        for step_data in form_step_data:
            form_definition_data = step_data.pop("form_definition")
            form_definition_configuration_data = form_definition_data["configuration"]

            for component in iter_components(form_definition_configuration_data):
                sanitize_component(component)

            form_definition_uuid = form_definition_data.pop("uuid")
            form_definition, _ = FormDefinition.objects.update_or_create(
                uuid=form_definition_uuid,
                defaults=form_definition_data,
            )

            FormStep.objects.create(
                **step_data, form_definition=form_definition, form=instance
            )

        return instance

    @transaction.atomic()
    def update(self, instance: Form, validated_data: dict[str, Any]) -> Form:
        form_step_data = validated_data.pop("formstep_set", [])

        instance = super().update(instance, validated_data)

        assigned_steps: list[FormStep] = []
        for step_data in form_step_data:
            form_definition_data = step_data.pop("form_definition")
            form_definition_configuration_data = form_definition_data["configuration"]

            for component in iter_components(form_definition_configuration_data):
                sanitize_component(component)

            form_definition_uuid = form_definition_data.pop("uuid")
            form_definition, _ = FormDefinition.objects.update_or_create(
                uuid=form_definition_uuid,
                defaults=form_definition_data,
            )

            step = FormStep(  # TODO: use update_or_create (nice to have)
                **step_data, form_definition=form_definition, form=instance
            )
            assigned_steps.append(step)

        steps_to_delete = instance.formstep_set.exclude(  # pyright: ignore[reportAttributeAccessIssue]
            pk__in=(step.pk for step in assigned_steps)
        )
        for step in steps_to_delete:
            step.delete()  # removes the form definition when applicable by calling `.delete`

        # Generate form steps after deleting existings steps, to allow correct calculation of
        # the `order` field.
        for step in sorted(assigned_steps, key=lambda step: step.order):
            step.save()
        return instance

    def validate_steps(self, value: list[FormStepData]) -> list[FormStepData]:
        definition_step_mapping: dict[UUID, list] = {}
        for step in value:
            current_steps = definition_step_mapping.setdefault(
                step["form_definition"]["uuid"], []
            )
            current_steps.append(step["order"])

        if any(len(values) > 1 for values in definition_step_mapping.values()):
            raise serializers.ValidationError(
                _("Non-unique form step - form definition combination(s) detected.")
            )

        for step in value:
            form_definition = step["form_definition"]
            other_form_definitions = [
                FakeFormDefinition(
                    configuration=cast(
                        dict[str, JSONValue],
                        other_step["form_definition"]["configuration"],
                    )
                )
                for other_step in value
                if other_step != step
            ]
            validate_no_duplicate_keys_across_steps(
                FakeFormDefinition(
                    configuration=cast(
                        dict[str, JSONValue],
                        form_definition["configuration"],
                    )
                ),
                other_form_definitions,
            )

        return value

    @transaction.atomic()
    def save(self, **kwargs):
        instance = super().save(**kwargs, uuid=self.context["form_uuid"])

        for step in instance.formstep_set.all():
            # call this synchronously so that it's part of the same DB transaction.
            FormVariable.objects.synchronize_for(step.form_definition)

        return instance
