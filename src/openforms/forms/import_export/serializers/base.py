from collections.abc import Sequence
from typing import ClassVar, TypedDict

from django.db.models import Model

from rest_framework import serializers

from ..typing import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
    FormExportOptions,
)


class BaseExportSerializer[MT: Model, RT: type[TypedDict]](serializers.Serializer):
    excluded_form_configuration_cleanup: ClassVar[
        Sequence[FormConfigurationCleanup[object]]
    ] = ()
    """
    Clean-up functions for form configuration.

    Clean-up functions that are called when excluding the specified form configuration
    during export. These functions specify how this configuration should be removed from
    the form data.
    """
    excluded_additional_form_configuration_cleanup: ClassVar[
        Sequence[AdditionalFormConfigurationCleanup[object]]
    ] = ()
    """
    Clean-up functions for additional form configuration.

    Clean-up functions that are called when excluding the specified additional form
    configuration during export. These functions specify how this configuration should
    be removed from the form data.
    """
    safe_export_fields: ClassVar[Sequence[str]] = ()
    """
    Fields that never contain sensitive information.

    When exporting with the option ``remove_sensitive_content=True``, only these fields
    will be exported.
    """

    def prepare_for_export(self, instance: MT):
        """
        A hook that is executed at the beginning of the export process.

        This hook can be used to prepare individual instances for export.
        """
        pass

    def to_representation(self, instance: MT):
        self.prepare_for_export(instance)
        representation = super().to_representation(instance)

        if self.get_export_options.remove_sensitive_content:
            representation = self.remove_sensitive_content(instance, representation)

        representation = self.remove_excluded_form_configuration(representation)
        representation = self.remove_excluded_additional_form_configuration(
            representation
        )

        return representation

    def remove_sensitive_content(self, instance: MT, representation: RT) -> RT:
        """
        Remove all fields that are not in the safe_export_fields list.
        """
        return {
            key: field
            for key, field in representation.items()
            if key in self.safe_export_fields
        }

    def remove_excluded_form_configuration(self, representation: RT) -> RT:
        options_to_keep = set(self.get_export_options.form_configuration)

        for config in self.excluded_form_configuration_cleanup:
            if config.option not in options_to_keep:
                config.cleanup(representation)

        return representation

    def remove_excluded_additional_form_configuration(self, representation: RT) -> RT:
        options_to_keep = set(self.get_export_options.additional_form_configuration)

        for config in self.excluded_additional_form_configuration_cleanup:
            if config.option not in options_to_keep:
                config.cleanup(representation)

        return representation

    @property
    def get_export_options(self) -> FormExportOptions:
        return self.context["export_options"]
