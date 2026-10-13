from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import time
from typing import Literal, override

import msgspec

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ..templating import TestWithTrace
from ..typing import ComponentValue

type TimeValidatorKeys = Literal["required", "minTime", "maxTime", "invalid_time"]
type TimeTranslatableProperties = Literal["label", "description", "tooltip"]

TimeExtensions = BaseOpenFormsExtensions[TimeTranslatableProperties]


class TimeValidate(FormioStruct):
    required: bool = False
    # a migration converter has fixed up empty strings to be null/None, but they're not
    # yet guaranteed to be in the HH:mm:ss format
    min_time: str | None = None
    max_time: str | None = None
    plugins: Sequence[str] = []


class Time(Component, tag="time"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    default_value: time | None | Sequence[time | None] = None
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TimeValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: TimeExtensions | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TimeValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: TimeValidate = msgspec.field(default_factory=TimeValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> time | None | Sequence[time | None] | msgspec.UnsetType:
        match (self.multiple, value):
            case False, time():
                return value
            case True, time() | None if strict:
                raise ValueError("You must pass a list of values when multiple=True")
            case True, Sequence():
                return [item for item in value if isinstance(item, time)]
            case False, Sequence() if strict:
                raise ValueError(
                    "You must pass a time default_value when multiple=False"
                )
            case _, None:
                return [] if self.multiple else None
        return msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)
        # we don't support templating default_value - this may have worked in the past,
        # but our builder has been active since 3.x which doesn't allow configuring
        # templates - and the JSON interface is not public API / supported to circumvent
        # these kind of limitations

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
