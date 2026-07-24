from django.urls import reverse

from openforms.config.models import Theme
from openforms.emails.utils import sanitize_content
from openforms.forms.api.serializers import FormSerializer
from openforms.forms.api.serializers.form import FormRegistrationBackendSerializer
from openforms.forms.constants import FormTypeChoices
from openforms.forms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
)
from openforms.forms.models import Category, Form
from openforms.typing import JSONObject

from .base import BaseExportSerializer, BaseImportSerializer


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


class FormImportSerializer(FormSerializer, BaseImportSerializer):
    excluded_additional_form_configuration_removal = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.yivi_attribute_groups,
            cleanup=clear_yivi_attribute_groups,
        ),
    )
    excluded_form_configuration_removal = (
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

    def to_internal_value(self, instance):
        value = instance.copy()

        value = self.set_theme(value)
        value = self.set_category(value)

        # We remove all unknown domains from the email templates
        value = self.sanitize_email_templates(value)

        # When importing a form, it should be non-active by default
        value["active"] = False

        return super().to_internal_value(value)

    def set_theme(self, value: JSONObject) -> JSONObject:
        if (import_options := self.get_import_options()) is not None and (
            theme := Theme.objects.filter(uuid=import_options.theme).first()
        ):
            theme_url = reverse("api:themes-detail", args=[theme.uuid])
            value["theme"] = theme_url
        else:
            value["theme"] = None

        return value

    def set_category(self, value: JSONObject) -> JSONObject:
        if (import_options := self.get_import_options()) is not None and (
            category := Category.objects.filter(uuid=import_options.category).first()
        ):
            category_url = reverse("api:categories-detail", args=[category.uuid])
            value["category"] = category_url
        else:
            value["category"] = None

        return value

    def apply_backwards_compatibility(self, value: JSONObject) -> JSONObject:
        # forms before v4.0 do not have the type field so in case we import an
        # old appointment form we have to make sure that the form has the right
        # type configured (by default is regular)
        # Original commit d8b1d4ea9d31772f059a388347e8a4688be5d717
        if appointment_options := value.get("appointment_options"):
            if appointment_options.get("is_appointment"):
                value["type"] = FormTypeChoices.appointment

        return value

    def sanitize_email_templates(self, value: JSONObject) -> JSONObject:
        # Sanitize confirmation email templates
        if value.get("confirmation_email_template", None) is not None:
            email_template = value["confirmation_email_template"]

            if email_template.get("content") is not None:
                email_template["content"] = sanitize_content(email_template["content"])

            if email_template.get("cosign_content") is not None:
                email_template["cosign_content"] = sanitize_content(
                    email_template["cosign_content"]
                )

            for translation in email_template.get("translations", {}).values():
                if translation.get("content") is not None:
                    translation["content"] = sanitize_content(translation["content"])

                if translation.get("cosign_content") is not None:
                    translation["cosign_content"] = sanitize_content(
                        translation["cosign_content"]
                    )

        # Sanitize email registration backend email templates
        for registration in value.get("registration_backends", []):
            if registration["backend"] == "email":
                options = registration["options"]

                if options.get("email_content_template_html") is not None:
                    options["email_content_template_html"] = sanitize_content(
                        options["email_content_template_html"]
                    )

                if options.get("email_content_template_text") is not None:
                    options["email_content_template_text"] = sanitize_content(
                        options["email_content_template_text"]
                    )

        return value
