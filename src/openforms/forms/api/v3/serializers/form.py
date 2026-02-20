from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.config.models.theme import Theme
from openforms.forms.api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from openforms.forms.api.v3.serializers.category import CategorySerializer
from openforms.forms.api.v3.serializers.product import ProductSerializer
from openforms.forms.api.v3.serializers.theme import ThemeSerializer
from openforms.forms.models.category import Category
from openforms.forms.models.form import Form
from openforms.products.models.product import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer


@extend_schema_serializer(component_name="FormV3Serializer")
class FormSerializer(serializers.ModelSerializer):
    product = ProductSerializer(required=False, allow_null=True)
    category = CategorySerializer(required=False, allow_null=True)
    theme = ThemeSerializer(required=False, allow_null=True)

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
            "url",
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
        )
        extra_kwargs = {
            "uuid": {
                "read_only": True,
            },
            "url": {
                "view_name": "api:v3:form-detail",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid",
            },
        }

    def _update_or_create_product(self, instance: Form, product_data: dict) -> None:
        product_uuid = product_data.pop("uuid")
        product, _ = Product.objects.update_or_create(
            uuid=product_uuid,
            defaults=product_data,
        )
        instance.product = product

    def _update_or_create_category(self, instance: Form, category_data: dict) -> None:
        category_uuid = category_data.pop("uuid")
        category, _ = Category.objects.update_or_create(
            uuid=category_uuid,
            defaults=category_data,
        )
        instance.category = category

    def _update_or_create_theme(self, instance: Form, theme_data: dict) -> None:
        theme_uuid = theme_data.pop("uuid")
        theme, _ = Theme.objects.update_or_create(
            uuid=theme_uuid,
            defaults=theme_data,
        )
        instance.theme = theme

    def create(self, validated_data: dict) -> Form:
        product_data = validated_data.pop("product", None)
        category_data = validated_data.pop("category", None)
        theme_data = validated_data.pop("theme", None)

        instance = super().create(validated_data)

        if product_data is not None:
            self._update_or_create_product(instance, product_data)
        if category_data is not None:
            self._update_or_create_category(instance, category_data)
        if theme_data is not None:
            self._update_or_create_theme(instance, theme_data)

        if any((product_data, category_data, theme_data)):
            instance.save()
        return instance

    def update(self, instance: Form, validated_data: dict) -> Form:
        product_data = validated_data.pop("product", None)
        category_data = validated_data.pop("category", None)
        theme_data = validated_data.pop("theme", None)

        instance = super().update(instance, validated_data)

        if product_data is not None:
            self._update_or_create_product(instance, product_data)
        if category_data is not None:
            self._update_or_create_category(instance, category_data)
        if theme_data is not None:
            self._update_or_create_theme(instance, theme_data)

        if any((product_data, category_data, theme_data)):
            instance.save()
        return instance

    def save(self, **kwargs):
        return super().save(**kwargs, uuid=self.context["uuid"])
