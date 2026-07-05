from openforms.forms.api.serializers import FormVariableSerializer
from openforms.import_export.typing import (
    FormConfigurationCleanup,
    FormConfigurationOptions,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.typing import JSONObject

from .base import BaseExportSerializer


def remove_prefill_from_variable(representation: JSONObject):
    representation["prefill_plugin"] = ""
    representation["prefill_attribute"] = ""
    representation["prefill_identifier_role"] = IdentifierRoles.main
    representation["prefill_options"] = {}


class FormVariableExportSerializer(FormVariableSerializer, BaseExportSerializer):
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup(
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_variable,
        ),
    )

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)
        form = instance.form

        for registration in form.registration_backends.all():
            if (
                registration.backend == "email"
                and "to_emails_from_variable" in registration.options
                and registration.options["to_emails_from_variable"]
                == representation["key"]
            ):
                representation["initial_value"] = ""
                return representation

        return representation
