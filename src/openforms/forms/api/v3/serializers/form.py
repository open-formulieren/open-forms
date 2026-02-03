from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models.theme import Theme
from openforms.forms.api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from openforms.forms.models.category import Category
from openforms.products.models.product import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer

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

    def save(self, **kwargs):
        return super().save(**kwargs, uuid=self.context["uuid"])
