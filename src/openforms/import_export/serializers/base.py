from rest_framework import serializers

from openforms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
    FormExportOptions,
    FormImportOptions,
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


class BaseImportSerializer(serializers.Serializer):
    excluded_form_configuration_removal: list[FormConfigurationCleanup] = ()
    excluded_additional_form_configuration_removal: list[
        AdditionalFormConfigurationCleanup
    ] = ()

    def to_internal_value(self, instance):
        value = instance.copy()
        value = self.apply_backwards_compatibility(value)

        value = self.remove_excluded_form_configuration(value)
        value = self.remove_excluded_additional_form_configuration(value)

        return super().to_internal_value(value)

    def apply_backwards_compatibility(self, value: dict[str, Any]) -> dict[str, Any]:
        return value

    def remove_excluded_form_configuration(self, value: JSONObject) -> JSONObject:
        selected_options = (
            set(import_options.form_configuration)
            if (import_options := self.get_import_options()) is not None
            else []
        )

        for config in self.excluded_form_configuration_removal:
            if config.option not in selected_options:
                config.cleanup(value)

        return value

    def remove_excluded_additional_form_configuration(
        self, value: JSONObject
    ) -> JSONObject:
        selected_options = (
            set(import_options.additional_form_configuration)
            if (import_options := self.get_import_options()) is not None
            else []
        )

        for config in self.excluded_additional_form_configuration_removal:
            if config.option not in selected_options:
                config.cleanup(value)

        return value

    def get_import_options(self) -> FormImportOptions | None:
        return self.context.get("import_options", None)
