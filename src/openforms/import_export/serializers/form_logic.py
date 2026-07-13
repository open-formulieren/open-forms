from openforms.forms.api.serializers import FormLogicSerializer
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

        return super().to_internal_value(value)
