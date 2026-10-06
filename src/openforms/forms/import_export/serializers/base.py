from collections.abc import Sequence
from typing import ClassVar, TypedDict

from django.db.models import Model

from rest_framework import serializers

from ..datastructures import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
    FormExportOptions,
)


class Representation(TypedDict):
    pass


class BaseExportSerializer[MT: Model, RT: Representation](serializers.Serializer):
    excluded_form_configuration_cleanup: ClassVar[
        Sequence[FormConfigurationCleanup]
    ] = ()
    """
    Clean-up functions for form configuration.

    Clean-up functions that are called when excluding the specified form configuration
    during export. These functions specify how this configuration should be removed from
    the form data.
    """
    excluded_additional_form_configuration_cleanup: ClassVar[
        Sequence[AdditionalFormConfigurationCleanup]
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

    def prepare_for_export(self, instance: MT) -> None:
        """
        A hook that is executed at the beginning of the export process.

        This hook can be used to prepare individual instances for export.
        """
        pass

    def to_representation(self, instance: MT) -> RT:  # pyright: ignore[reportIncompatibleMethodOverride]
        self.prepare_for_export(instance)
        from typing import cast  # noqa: TID251

        # DRF upstream types (dict[str, Any]) are not compatible with TypedDict, this is
        # a valid exception to get some grip on type safety
        representation = cast(RT, super().to_representation(instance))

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
        cleaned_representation: RT = representation.copy()
        for key in list(cleaned_representation):
            if key not in self.safe_export_fields:
                del cleaned_representation[key]
        return cleaned_representation

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


class BaseImportSerializer[RT: Representation](serializers.Serializer):
    def to_internal_value(self, instance: RT) -> RT:
        value = instance.copy()
        return super().to_internal_value(value)
