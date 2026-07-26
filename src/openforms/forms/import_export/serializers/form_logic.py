from ...api.serializers import FormLogicSerializer
from ...models import FormLogic
from .base import BaseExportSerializer


class FormLogicExportSerializer(FormLogicSerializer, BaseExportSerializer[FormLogic]):
    safe_export_fields = (
        "uuid",
        "url",
        "form",
        "json_logic_trigger",
        "description",
        "order",
        "actions",
        "is_advanced",
        "form_steps",
    )

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)
        form = instance.form

        # TODO move this to a registration backend options specific implementation
        # Preventing the removal or naming of options to break this functionality
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
