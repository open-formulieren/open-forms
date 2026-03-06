from typing import Any

from django.db import transaction

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models.theme import Theme
from openforms.emails.api.serializers import ConfirmationEmailTemplateSerializer
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.products.models.product import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer

from ....api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from ....models.category import Category
from ....models.form import Form


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

    @transaction.atomic()
    def create(self, validated_data: dict[str, Any]) -> Form:
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        instance = super().create(validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        return instance

    @transaction.atomic()
    def update(self, instance, validated_data: dict[str, Any]) -> Form:
        confirmation_email_template = validated_data.pop(
            "confirmation_email_template", None
        )
        instance = super().update(instance, validated_data)
        ConfirmationEmailTemplate.objects.set_for_form(
            form=instance, data=confirmation_email_template
        )
        return instance

    def save(self, **kwargs):
        return super().save(**kwargs, uuid=self.context["uuid"])
