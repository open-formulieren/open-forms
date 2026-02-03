from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_array_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from openforms.appointments.api.serializers import AppointmentOptionsSerializer
from openforms.authentication.api.fields import LoginOptionsReadOnlyField
from openforms.config.api.constants import STATEMENT_CHECKBOX_SCHEMA
from openforms.config.models.config import GlobalConfiguration
from openforms.config.models.theme import Theme
from openforms.formio.typing.base import Component
from openforms.forms.api.serializers.form import (
    FormLiteralsSerializer,
    SubmissionsRemovalOptionsSerializer,
)
from openforms.forms.constants import StatementCheckboxChoices
from openforms.forms.models.category import Category
from openforms.forms.models.form import Form
from openforms.products.models.product import Product
from openforms.translations.api.serializers import ModelTranslationsSerializer


@extend_schema_serializer(component_name="FormV3Serializer")
class FormSerializer(serializers.ModelSerializer):
    login_options = LoginOptionsReadOnlyField()
    cosign_login_options = LoginOptionsReadOnlyField(is_for_cosign=True)
    cosign_has_link_in_email = serializers.SerializerMethodField(
        label=_("cosign request has links in email"),
        help_text=_(
            "Indicates whether deep links are included in the cosign request emails "
            "or not."
        ),
    )

    product = serializers.HyperlinkedRelatedField(
        label=_("product"),
        queryset=Product.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:product-detail",
        lookup_field="uuid",
        help_text=_("URL to the product in the Open Forms API"),
    )
    category = serializers.HyperlinkedRelatedField(
        label=_("category"),
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:categories-detail",
        lookup_field="uuid",
        help_text=_("URL to the category in the Open Forms API"),
    )
    theme = serializers.HyperlinkedRelatedField(
        label=_("theme"),
        queryset=Theme.objects.all(),
        required=False,
        allow_null=True,
        view_name="api:themes-detail",
        lookup_field="uuid",
        help_text=_("URL to the theme in the Open Forms API"),
    )

    appointment_options = AppointmentOptionsSerializer(
        source="*",
        required=False,
        allow_null=True,
    )

    literals = FormLiteralsSerializer(source="*", required=False)

    is_deleted = serializers.BooleanField(source="_is_deleted", required=False)
    required_fields_with_asterisk = serializers.SerializerMethodField(read_only=True)
    resume_link_lifetime = serializers.SerializerMethodField(
        label=_("Resume link lifetime"),
        read_only=True,
        help_text=_("The number of days that the resume link is valid for."),
    )
    communication_preferences_portal_url = serializers.SerializerMethodField(
        read_only=True
    )
    hide_non_applicable_steps = serializers.SerializerMethodField(read_only=True)
    submission_report_download_link_title = serializers.SerializerMethodField()
    submission_statements_configuration = serializers.SerializerMethodField(
        label=_("submission statements configuration"),
        help_text=_(
            "A list of statements that need to be accepted by the user before they "
            "can submit a form. Returns a list of formio component definitions, all "
            "of type 'checkbox'."
        ),
    )

    submission_limit_reached = serializers.SerializerMethodField()
    submissions_removal_options = SubmissionsRemovalOptionsSerializer(
        source="*", required=False
    )

    translations = ModelTranslationsSerializer()

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "internal_remarks",
            "login_required",
            "translation_enabled",
            "login_options",
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
            "submission_limit_reached",
            "suspension_allowed",
            "ask_privacy_consent",
            "ask_statement_of_truth",
            "submissions_removal_options",
            "send_confirmation_email",
            "display_main_website_link",
            "include_confirmation_page_content_in_pdf",
            "required_fields_with_asterisk",
            "communication_preferences_portal_url",
            "translations",
            "resume_link_lifetime",
            "hide_non_applicable_steps",
            "cosign_login_options",
            "cosign_has_link_in_email",
            "submission_statements_configuration",
            "submission_report_download_link_title",
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

    def save(self, **kwargs):
        return super().save(**kwargs, uuid=self.context["uuid"])

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_cosign_has_link_in_email(self, obj: Form) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.cosign_request_template_has_link

    def get_submission_limit_reached(self, obj: Form) -> bool:
        return obj.submissions_limit_reached

    def get_required_fields_with_asterisk(self, obj: Form) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.form_display_required_with_asterisk

    def get_communication_preferences_portal_url(self, obj: Form) -> str:
        config = GlobalConfiguration.get_solo()
        return config.communication_preferences_portal_url

    def get_hide_non_applicable_steps(self, obj: Form) -> bool:
        config = GlobalConfiguration.get_solo()
        return config.hide_non_applicable_steps

    def get_submission_report_download_link_title(self, obj: Form) -> str:
        config = GlobalConfiguration.get_solo()
        return config.submission_report_download_link_title

    @extend_schema_field(field=build_array_type(STATEMENT_CHECKBOX_SCHEMA))
    def get_submission_statements_configuration(self, obj: Form) -> list[Component]:
        config = GlobalConfiguration.get_solo()

        ask_privacy_consent = (
            obj.ask_privacy_consent == StatementCheckboxChoices.required
            or (
                obj.ask_privacy_consent == StatementCheckboxChoices.global_setting
                and config.ask_privacy_consent
            )
        )
        ask_statement_of_truth = (
            obj.ask_statement_of_truth == StatementCheckboxChoices.required
            or (
                obj.ask_statement_of_truth == StatementCheckboxChoices.global_setting
                and config.ask_statement_of_truth
            )
        )

        # TODO Generalise to configurable declarations
        privacy_policy_checkbox = Component(
            key="privacyPolicyAccepted",
            label=config.render_privacy_policy_label(),
            validate={"required": ask_privacy_consent},
            type="checkbox",
        )
        truth_declaration_checkbox = Component(
            key="statementOfTruthAccepted",
            label=config.statement_of_truth_label,
            validate={"required": ask_statement_of_truth},
            type="checkbox",
        )

        return [privacy_policy_checkbox, truth_declaration_checkbox]

    def get_resume_link_lifetime(self, obj: Form) -> int:
        config = GlobalConfiguration.get_solo()
        lifetime = (
            obj.incomplete_submissions_removal_limit
            or config.incomplete_submissions_removal_limit
        )
        lifetime_all = (
            obj.all_submissions_removal_limit or config.all_submissions_removal_limit
        )
        lifetime = min(lifetime, lifetime_all)

        return lifetime
