from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TypedDict

from openforms.typing import JSONObject

from .constants import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)


# This is needed for the form bulk export Celery task.
# Any other place where export options are needed should use FormExportOptions.
class FormExportOptionsData(TypedDict, total=False):
    remove_sensitive_content: bool
    form_configuration: Sequence[FormConfigurationOptions]
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions]


@dataclass(slots=True)
class FormExportOptions:
    remove_sensitive_content: bool = True
    form_configuration: Sequence[FormConfigurationOptions] = field(
        default_factory=lambda: [
            FormConfigurationOptions.registration_backends,
            FormConfigurationOptions.prefill,
            FormConfigurationOptions.payment_backend,
            FormConfigurationOptions.auth_backends,
        ]
    )
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class AdditionalFormConfigurationCleanup:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[JSONObject], None]


@dataclass(frozen=True)
class FormConfigurationCleanup:
    option: FormConfigurationOptions
    cleanup: Callable[[JSONObject], None]
