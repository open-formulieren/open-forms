from rest_framework import serializers

from openforms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
    FormExportOptions,
)
from openforms.typing import JSONObject


class BaseExportSerializer(serializers.Serializer):
    excluded_form_configuration_cleanup: list[FormConfigurationCleanup] = ()
    excluded_additional_form_configuration_cleanup: list[
        AdditionalFormConfigurationCleanup
    ] = ()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if (
            export_options := self.get_export_options()
        ) is not None and export_options.remove_sensitive_content:
            representation = self.remove_sensitive_content(instance, representation)

        representation = self.remove_excluded_form_configuration(representation)
        representation = self.remove_excluded_additional_form_configuration(
            representation
        )

        return representation

    def remove_sensitive_content(
        self, instance, representation: JSONObject
    ) -> JSONObject:
        return representation

    def remove_excluded_form_configuration(
        self, representation: JSONObject
    ) -> JSONObject:
        selected_options = (
            set(export_options.form_configuration)
            if (export_options := self.get_export_options()) is not None
            else []
        )

        for config in self.excluded_form_configuration_cleanup:
            if config.option not in selected_options:
                config.cleanup(representation)

        return representation

    def remove_excluded_additional_form_configuration(
        self, representation: JSONObject
    ) -> JSONObject:
        selected_options = (
            set(export_options.additional_form_configuration)
            if (export_options := self.get_export_options()) is not None
            else []
        )

        for config in self.excluded_additional_form_configuration_cleanup:
            if config.option not in selected_options:
                config.cleanup(representation)

        return representation

    def get_export_options(self) -> FormExportOptions | None:
        return self.context.get("export_options", None)
