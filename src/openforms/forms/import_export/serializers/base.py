from rest_framework import serializers

from openforms.typing import JSONObject

from ..typing import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
    FormExportOptions,
)


class BaseExportSerializer(serializers.Serializer):
    excluded_form_configuration_cleanup: list[FormConfigurationCleanup] = ()
    excluded_additional_form_configuration_cleanup: list[
        AdditionalFormConfigurationCleanup
    ] = ()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if self.get_export_options.remove_sensitive_content:
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
        options_to_keep = set(self.get_export_options.form_configuration)

        for config in self.excluded_form_configuration_cleanup:
            if config.option not in options_to_keep:
                config.cleanup(representation)

        return representation

    def remove_excluded_additional_form_configuration(
        self, representation: JSONObject
    ) -> JSONObject:
        options_to_keep = set(self.get_export_options.additional_form_configuration)

        for config in self.excluded_additional_form_configuration_cleanup:
            if config.option not in options_to_keep:
                config.cleanup(representation)

        return representation

    @property
    def get_export_options(self) -> FormExportOptions:
        return self.context["export_options"]
