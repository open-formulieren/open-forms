from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import time
from typing import Literal, assert_never

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
    # FIXME: should be time instances, but can't deserialize empty string into a valid
    # time, nor is conversion to non viable at this point.
    min_time: str | None = ""
    max_time: str | None = ""


class Time(Component, tag="time"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # FIXME: properly parse this into ``time`` instances, but then we need to
    # pre-process for empty strings & add ``null`` to the allowed types in the frontend.
    default_value: str | Sequence[str] = ""
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
            case True, str():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case time() if not self.multiple:
                self.default_value = value.isoformat()
            case Sequence() if self.multiple:
                self.default_value = [
                    item.isoformat() for item in value if isinstance(item, time)
                ]
            case None:
                self.default_value = [] if self.multiple else ""
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

        match self.default_value:
            case str():
                self.default_value = do_render(self.default_value)
            case Sequence():
                self.default_value = [do_render(v) for v in self.default_value]
            case _:  # pragma: no cover
                assert_never(self.default_value)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")

        normalized = (
            self.default_value
            if isinstance(self.default_value, Sequence)
            else [self.default_value]
        )
        for _value in normalized:
            test_with_trace(_value, attribute="default_value")
