from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import time
from typing import Literal

import msgspec
import structlog

from openforms.typing import VariableValue

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)

type TimeValidatorKeys = Literal["required", "minTime", "maxTime", "invalid_time"]
type TimeTranslatableProperties = Literal["label", "description", "tooltip"]

TimeExtensions = BaseOpenFormsExtensions[TimeTranslatableProperties]


class DateTimeValidate(FormioStruct):
    required: bool = False
    # a migration converter has fixed up empty strings to be null/None, but they're not
    # yet guaranteed to be in the HH:mm:ss format
    min_time: str | None = None
    max_time: str | None = None


class Time(Component, tag="time"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: time | None | Sequence[time | None] = None
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TimeValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: TimeExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TimeValidatorKeys] | None = None
    validate: DateTimeValidate = msgspec.field(default_factory=DateTimeValidate)

    def __post_init__(self):
        match (self.multiple, self.default_value):
            case True, time():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, time():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case time() if not self.multiple:
                self.default_value = value
            case Sequence() if self.multiple:
                self.default_value = [item for item in value if isinstance(item, time)]
            case None:
                self.default_value = [] if self.multiple else None
            case _:
                logger.warning(
                    "received_invalid_default_value",
                    component=str(type(self)),
                    value=value,
                    multiple=self.multiple,
                )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)
        # we don't support templating default_value - this may have worked in the past,
        # but our builder has been active since 3.x which doesn't allow configuring
        # templates - and the JSON interface is not public API / supported to circumvent
        # these kind of limitations

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
