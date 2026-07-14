from openforms.forms.api.serializers import FormLogicSerializer
from openforms.forms.constants import LogicActionTypes
from openforms.import_export.serializers.base import (
    BaseExportSerializer,
    BaseImportSerializer,
)


class FormLogicExportSerializer(FormLogicSerializer, BaseExportSerializer):
    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)
        form = instance.form

        sensitive_variables = (
            registration.options["to_emails_from_variable"]
            for registration in form.registration_backends.all()
            if registration.backend == "email"
            and "to_emails_from_variable" in registration.options
        )

        for action in representation["actions"]:
            if (
                action["action"]["type"] == "variable"
                and action["variable"] in sensitive_variables
            ):
                action["action"]["value"] = ""

        return representation


class FormLogicImportSerializer(FormLogicSerializer, BaseImportSerializer):
    def to_internal_value(self, instance):
        value = instance.copy()

        if "order" not in value:
            value["order"] = 0

        # @TODO this was AFTER validation. So maybe in a to_representation call?
        self.clear_old_service_fetch_config(value)

        return super().to_internal_value(value)

    def clear_old_service_fetch_config(self, rule: dict) -> None:
        for action in rule["actions"]:
            if action["action"]["type"] != LogicActionTypes.fetch_from_service:
                continue

            if "value" not in action["action"] or action["action"]["value"] == "":
                continue

            # See comment above in `import_form_data` where we check if the variable has a
            # `service_fetch_configuration` attribute.
            # We can't reliably relate the service fetch configured to an existing configuration.
            # So we don't add any existing service fetch config to the variables
            action["action"]["value"] = ""
