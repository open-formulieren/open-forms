import random
import string

import structlog

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

from ...api.serializers import FormSerializer
from ...api.serializers.form import (
    FormAuthenticationBackendSerializer,
    FormRegistrationBackendSerializer,
)
from ...constants import FormTypeChoices
from ...models import Form, FormRegistrationBackend
from ..constants import AdditionalFormConfigurationOptions, FormConfigurationOptions
from ..datastructures import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
)
from ..typing import FormData, FormRegistrationData
from .base import BaseExportSerializer, BaseImportSerializer

logger = structlog.stdlib.get_logger(__name__)


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
    excluded_additional_form_configuration_removal = (
        AdditionalFormConfigurationCleanup[FormData](
            option=AdditionalFormConfigurationOptions.product,
            cleanup=clear_product,
        ),
        AdditionalFormConfigurationCleanup[FormData](
            option=AdditionalFormConfigurationOptions.yivi_attribute_groups,
            cleanup=clear_yivi_attribute_groups,
        ),
    )
    excluded_form_configuration_removal = (
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

    def apply_backwards_compatibility(self, data: FormData) -> FormData:
        self.apply_backwards_compatibility_appointment_type(data)
        self.apply_backwards_compatibility_authentication_backends(data)
        self.apply_backwards_compatibility_convert_objects_api_group(data)

        return data

    def apply_backwards_compatibility_appointment_type(self, data: FormData) -> None:
        """
        Backwards compatibility for using old appointment form configuration.

        forms before v4.0 do not have the type field so in case we import an
        old appointment form we have to make sure that the form has the right
        type configured (by default is regular)

        Original commit d8b1d4ea9d31772f059a388347e8a4688be5d717
        """
        if appointment_options := data.get("appointment_options"):
            if appointment_options.get("is_appointment"):
                data["type"] = FormTypeChoices.appointment

    def apply_backwards_compatibility_authentication_backends(
        self, data: FormData
    ) -> None:
        """
        Backwards compatibility for using old authentication_backends configuration.

        In v3.2 the authentication_backends field was replaced with auth_backends. This
        converter ensures that pre-v3.2 forms are converted correctly. See #5140

        Original commit d08281dad2e426e2655d87f67cefec9b58c5c810
        """
        if (
            "authentication_backends" not in data
            and "authentication_backend_options" not in data
        ):
            return

        # Make sure `auth_backends` exists
        data["auth_backends"] = data.get("auth_backends", [])
        auth_backends_map = {}

        # Pre-fill the map with the `auth_backends` values
        for auth_backend in data["auth_backends"]:
            auth_backends_map[auth_backend["backend"]] = auth_backend

        # Collect all the backends that should be transformed to `auth_backends`
        if "authentication_backends" in data:
            for plugin in data["authentication_backends"]:
                # Add plugin if it's not already in the map
                if plugin not in auth_backends_map:
                    auth_backends_map[plugin] = {
                        "backend": plugin,
                        "options": None,
                    }

        if "authentication_backend_options" in data:
            for plugin, options in data["authentication_backend_options"].items():
                if plugin not in auth_backends_map:
                    auth_backends_map[plugin] = {
                        "backend": plugin,
                        "options": options,
                    }
                    continue

                if auth_backends_map[plugin]["options"] is None:
                    auth_backends_map[plugin]["options"] = options

        validated_auth_backends = []
        for config in auth_backends_map.values():
            validated_auth_backends.append(
                FormAuthenticationBackendSerializer().validate(config)
            )
        data["auth_backends"] = validated_auth_backends

    def apply_backwards_compatibility_convert_objects_api_group(
        self, data: FormData
    ) -> None:
        """
        Backwards compatibility for using objects_api_group as pk in the form registration backends
        see GH issue #5384.

        Original commit db494a19544f196e54821d2d390f78c5e419bdd8
        """
        if "registration_backends" not in data:
            return

        objects_api_pk_to_slug = {
            group.pk: group.identifier for group in ObjectsAPIGroupConfig.objects.all()
        }
        for plugin in data["registration_backends"]:
            options = plugin.get("options", {})
            if not (api_group_id := options.get("objects_api_group")):
                continue

            if isinstance(api_group_id, int):
                api_group_slug = objects_api_pk_to_slug[api_group_id]
                options["objects_api_group"] = api_group_slug
                logger.info(
                    "objects_api_group_reference_converted",
                    from_pk=api_group_id,
                    to_identifier=api_group_slug,
                )
