from urllib.parse import urlsplit

from mail_cleaner.constants import URL_REGEX

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import get_netloc_allowlist, sanitize_content
from openforms.emails.validators import subdomains
from openforms.forms.api.serializers import FormSerializer
from openforms.forms.constants import FormTypeChoices
from openforms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
    LinksToUnknownDomainsOptions,
)
from openforms.typing import JSONObject

from .base import BaseExportSerializer, BaseImportSerializer


def clear_product(representation: JSONObject):
    representation["product"] = None


def clear_category(representation: JSONObject):
    representation["category"] = None


def clear_theme(representation: JSONObject):
    representation["theme"] = None


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


class FormExportSerializer(FormSerializer, BaseExportSerializer):
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.category,
            cleanup=clear_category,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.theme,
            cleanup=clear_theme,
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
    )

    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        if "login_options" in fields:
            del fields["login_options"]
        if "payment_options" in fields:
            del fields["payment_options"]
        return fields

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)
        representation["internal_remarks"] = ""

        for registration in representation.get("registration_backends", []):
            if registration["backend"] == "email":
                registration["options"]["to_emails"] = []
                registration["options"]["payment_emails"] = []

        return representation


class FormImportSerializer(FormSerializer, BaseImportSerializer):
    excluded_additional_form_configuration_removal = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.category,
            cleanup=clear_category,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.theme,
            cleanup=clear_theme,
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
        value = self.handle_unknown_domains(value)

        # When importing a form, it should be non-active by default
        value["active"] = False

        return super().to_internal_value(value)

    def apply_backwards_compatibility(self, value: JSONObject) -> JSONObject:
        # forms before v4.0 do not have the type field so in case we import an
        # old appointment form we have to make sure that the form has the right
        # type configured (by default is regular)
        if appointment_options := value.get("appointment_options"):
            if appointment_options.get("is_appointment"):
                value["type"] = FormTypeChoices.appointment

        return value

    def handle_unknown_domains(self, value: JSONObject) -> JSONObject:
        if (import_options := self.get_import_options()) is None:
            return value

        match import_options.links_to_unknown_domains:
            case LinksToUnknownDomainsOptions.accept:
                # Collect all unique unknown domains and add them to the allowed domains
                self.accept_all_unknown_domains(value)

            case LinksToUnknownDomainsOptions.remove:
                # Remove all unknown domains from the email templates
                return self.sanitize_email_templates(value)

            case LinksToUnknownDomainsOptions.ignore:
                pass

            case _:  # pragma: no cover
                raise RuntimeError(
                    f"Unknown 'links_to_unknown_domains' import option: {import_options.links_to_unknown_domains}"
                )

        return value

    def get_unknown_domains(self, value: str) -> list[str]:
        allowlist = get_netloc_allowlist()
        unknown_domains = []

        for m in URL_REGEX.finditer(value):
            parsed = urlsplit(m.group())

            if not any(stem for stem in subdomains(parsed.netloc) if stem in allowlist):
                unknown_domains.append(parsed.netloc)

        return unknown_domains

    def accept_all_unknown_domains(self, value: JSONObject):
        global_config = GlobalConfiguration.get_solo()

        # Get the unknown domains from the confirmation email template
        all_unknown_domains = [
            *self.get_unknown_domains(
                value.get("confirmation_email_template", {}).get("content", "")
            ),
            *self.get_unknown_domains(
                value.get("confirmation_email_template", {}).get("cosign_content", "")
            ),
        ]

        # Get the unknown domains from the email registration backends
        for registration in value.get("registration_backends", []):
            if registration["backend"] == "email":
                options = registration.get("options", {})
                all_unknown_domains.extend(
                    [
                        *self.get_unknown_domains(
                            options.get("email_content_template_html", "")
                        ),
                        *self.get_unknown_domains(
                            options.get("email_content_template_text", "")
                        ),
                    ]
                )

        # Get all unique unknown domains and add them all to the allowlist
        global_config.email_template_netloc_allowlist.extend(
            list(set(all_unknown_domains))
        )

        global_config.save()

    def sanitize_email_templates(self, value: JSONObject) -> JSONObject:
        # Sanitize confirmation email templates
        if value.get("confirmation_email_template", None) is not None:
            value["confirmation_email_template"]["content"] = sanitize_content(
                value["confirmation_email_template"].get("content", "")
            )
            value["confirmation_email_template"]["cosign_content"] = sanitize_content(
                value["confirmation_email_template"].get("cosign_content", "")
            )
            for translation in (
                value["confirmation_email_template"].get("translations", {}).values()
            ):
                translation["content"] = sanitize_content(
                    translation.get("content", "")
                )
                translation["cosign_content"] = sanitize_content(
                    translation.get("cosign_content", "")
                )

        # Sanitize email registration backend email templates
        for registration in value.get("registration_backends", []):
            if registration["backend"] == "email":
                registration["options"]["email_content_template_html"] = (
                    sanitize_content(
                        registration["options"].get("email_content_template_html", "")
                    )
                )
                registration["options"]["email_content_template_text"] = (
                    sanitize_content(
                        registration["options"].get("email_content_template_text", "")
                    )
                )

        return value
