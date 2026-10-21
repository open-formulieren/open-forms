from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from openforms.config.models import Theme

from ..models import Category
from .constants import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)


@dataclass(frozen=True)
class AdditionalFormConfigurationCleanup[RT]:
    option: AdditionalFormConfigurationOptions
    cleanup: Callable[[RT], None]


@dataclass(frozen=True)
class FormConfigurationCleanup[RT]:
    option: FormConfigurationOptions
    cleanup: Callable[[RT], None]


@dataclass(slots=True)
class FormExportOptions:
    remove_sensitive_content: bool = True
    form_configuration: Sequence[FormConfigurationOptions] = field(
        default_factory=lambda: list(FormConfigurationOptions)
    )
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )


@dataclass(slots=True)
class FormImportOptions:
    form_configuration: Sequence[FormConfigurationOptions] = field(
        default_factory=lambda: list(FormConfigurationOptions)
    )
    additional_form_configuration: Sequence[AdditionalFormConfigurationOptions] = field(
        default_factory=list
    )
    theme: Theme | None = None
    category: Category | None = None
