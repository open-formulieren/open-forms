from openforms.forms.api.serializers import FormSerializer
from openforms.forms.api.serializers.form import FormRegistrationBackendSerializer
from openforms.forms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
)
from openforms.typing import JSONObject

from .base import BaseExportSerializer


def clear_product(representation: JSONObject):
    representation["product"] = None


def clear_yivi_attribute_groups(representation: JSONObject):
    for auth in representation.get("auth_backends", []):
        if auth["backend"] == "yivi_oidc":
            auth["options"]["additional_attributes_groups"] = []


def exclude_registration_backends(representation: JSONObject):
    representation["registration_backends"] = []


def exclude_payment_backend(representation: JSONObject):
    representation["payment_backend"] = ""
    representation["payment_backend_options"] = {}


def exclude_auth_backends(representation: JSONObject):
    representation["auth_backends"] = []


class FormRegistrationBackendExportSerializer(
    FormRegistrationBackendSerializer, BaseExportSerializer
):
    save_export_fields = (
        "key",
        "name",
        "backend",
        "options",
    )

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)

        if representation["backend"] == "email":
            representation["options"]["to_emails"] = []
            representation["options"]["payment_emails"] = []

        return representation


class FormExportSerializer(FormSerializer, BaseExportSerializer):
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.yivi_attribute_groups,
            cleanup=clear_yivi_attribute_groups,
        ),
    )
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup(
            option=FormConfigurationOptions.registration_backends,
            cleanup=exclude_registration_backends,
        ),
        FormConfigurationCleanup(
            option=FormConfigurationOptions.payment_backend,
            cleanup=exclude_payment_backend,
        ),
        FormConfigurationCleanup(
            option=FormConfigurationOptions.auth_backends,
            cleanup=exclude_auth_backends,
        ),
    )
    registration_backends = FormRegistrationBackendExportSerializer(
        many=True, required=False
    )
    save_export_fields = (
        "uuid",
        "name",
        "internal_name",
        "login_required",
        "translation_enabled",
        "registration_backends",
        "auth_backends",
        "login_options",
        "auto_login_authentication_backend",
        "payment_required",
        "payment_backend",
        "payment_backend_options",
        "payment_options",
        "price_variable_key",
        "appointment_options",
        "literals",
        "begin_text",
        "previous_text",
        "change_text",
        "confirm_text",
        "product",
        "slug",
        "url",
        "type",
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
        "submission_limit_reached",
        "suspension_allowed",
        "ask_privacy_consent",
        "ask_statement_of_truth",
        "submissions_removal_options",
        "confirmation_email_template",
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
        "brp_personen_request_options",
    )

    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        if "login_options" in fields:
            del fields["login_options"]
        if "payment_options" in fields:
            del fields["payment_options"]
        return fields
