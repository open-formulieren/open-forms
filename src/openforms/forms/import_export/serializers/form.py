from openforms.forms.api.serializers import FormSerializer
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
