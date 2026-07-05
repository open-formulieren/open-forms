from rest_framework import serializers

from openforms.import_export.typing import FormExportOptions
from openforms.typing import JSONObject


class BaseExportSerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if (
            export_options := self.get_export_options()
        ) is not None and export_options.remove_sensitive_content:
            representation = self.remove_sensitive_content(instance, representation)

        return representation

    def remove_sensitive_content(
        self, instance, representation: JSONObject
    ) -> JSONObject:
        return representation

    def get_export_options(self) -> FormExportOptions | None:
        return self.context.get("export_options", None)
