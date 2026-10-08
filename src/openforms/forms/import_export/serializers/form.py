import random
import string

from ...api.serializers import FormSerializer
from ...api.serializers.form import FormRegistrationBackendSerializer
from ...models import Form, FormRegistrationBackend
from ..constants import AdditionalFormConfigurationOptions, FormConfigurationOptions
from ..datastructures import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
)
from ..typing import FormData, FormRegistrationData
from .base import BaseExportSerializer, BaseImportSerializer


def clear_product(data: FormData):
    """
    Remove product data the form configuration.

    :param data: FormData The Form data as dict. This could be either the representation
    of data to be exported or data to be imported.
    """
    data["product"] = ""


def clear_yivi_attribute_groups(data: FormData):
    """
    Remove the Yivi attribute groups from any possible Yivi authentication backends.

    :param data: FormData The Form data as dict. This could be either the representation
    of data to be exported or data to be imported.
    """
    for auth in data.get("auth_backends", []):
        if auth["backend"] == "yivi_oidc":
            auth["options"]["additional_attributes_groups"] = []


def exclude_registration_backends(data: FormData):
    """
    Remove all registration backends from the form configuration.

    :param data: FormData The Form data as dict. This could be either the representation
    of data to be exported or data to be imported.
    """
    data["registration_backends"] = []


def exclude_payment_backend(data: FormData):
    """
    Remove the payment backend from the form configuration.

    :param data: FormData The Form data as dict. This could be either the representation
    of data to be exported or data to be imported.
    """
    data["payment_backend"] = ""
    data["payment_backend_options"] = {}


def exclude_auth_backends(data: FormData):
    """
    Remove all authentication backends from the form configuration.

    :param data: FormData The Form data as dict. This could be either the representation
    of data to be exported or data to be imported.
    """
    data["auth_backends"] = []


class FormRegistrationBackendExportSerializer(
    FormRegistrationBackendSerializer,
    BaseExportSerializer[FormRegistrationBackend, FormRegistrationData],
):
    safe_export_fields = (
        "key",
        "name",
        "backend",
        "options",
    )

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)

        # TODO move this to a registration backend options specific implementation
        # Preventing the removal or naming of options to break this functionality
        if representation["backend"] == "email":
            representation["options"]["to_emails"] = []
            representation["options"]["payment_emails"] = []

        return representation


class FormExportSerializer(FormSerializer, BaseExportSerializer[Form, FormData]):
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup[FormData](
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup[FormData](
            option=AdditionalFormConfigurationOptions.yivi_attribute_groups,
            cleanup=clear_yivi_attribute_groups,
        ),
    )
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup[FormData](
            option=FormConfigurationOptions.registration_backends,
            cleanup=exclude_registration_backends,
        ),
        FormConfigurationCleanup[FormData](
            option=FormConfigurationOptions.payment_backend,
            cleanup=exclude_payment_backend,
        ),
        FormConfigurationCleanup[FormData](
            option=FormConfigurationOptions.auth_backends,
            cleanup=exclude_auth_backends,
        ),
    )
    registration_backends = FormRegistrationBackendExportSerializer(
        many=True, required=False
    )
    safe_export_fields = (
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

    def prepare_for_export(self, instance: Form) -> None:
        # Reset the submission counter
        instance.submission_counter = 0

    def get_fields(self):
        fields = super().get_fields()
        # for export we want to use the list of plugin-id's instead of detailed info objects
        if "login_options" in fields:
            del fields["login_options"]
        if "payment_options" in fields:
            del fields["payment_options"]
        return fields


class FormImportSerializer(FormSerializer, BaseImportSerializer[Form, FormData]):
    def prepare_for_import(self, data: FormData) -> FormData:
        # When importing a form, it should be non-active by default
        data["active"] = False

        self.set_category(data)
        self.set_theme(data)

        # If there is a slug, make sure that it's unique
        if form_slug := data.get("slug"):
            self.uniquify_slug(data, form_slug)

        return data

    def set_theme(self, data: FormData) -> None:
        """
        Make sure that the imported form does not have an unknown theme set.

        This helps prevent common import errors.
        """
        # theme overrides cannot be imported, since the theme records/FKs have to
        # exist in the target environment. Importing/exporting themes is also not
        # possible at this time, so we reset the theme and admins need to update
        # the imported form.
        data["theme"] = ""

    def set_category(self, data: FormData) -> None:
        """
        Make sure that the imported form does not have an unknown category set.

        This helps prevent common import errors.
        """
        # we can only extract a category UUID from the URL here, but that requires
        # an exact match and we currently don't provide import/export functionality
        # for categories. Relying on ID/Name is not much better than guesswork either,
        # so we always import forms with NO category at all to prevent import errors.
        # See #1774 for one such example of an error.
        data["category"] = ""

    @staticmethod
    def uniquify_slug(data: FormData, slug: str) -> None:
        """
        Make sure that the imported form uses a unique slug before we import it.

        This helps prevent common import errors.
        """
        if Form.objects.filter(slug=slug).first() is not None:
            data["slug"] = f"{slug}-{''.join(random.choices(string.hexdigits, k=6))}"
