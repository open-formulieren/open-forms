from openforms.forms.api.serializers import FormSerializer

from .base import BaseExportSerializer


class FormExportSerializer(FormSerializer, BaseExportSerializer):
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
