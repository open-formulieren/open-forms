from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Literal, override

import msgspec
import structlog

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Key,
    Prefill,
    Registration,
    Sentinel,
    TranslatedErrors,
    unset,
)
from ..templating import TestWithTrace
from ..typing import ComponentValue

logger = structlog.stdlib.get_logger(__name__)


class NoDateConstraint(FormioStruct, tag="", tag_field="mode"):
    pass


class FixedValueDateConstraint(FormioStruct, tag="fixedValue", tag_field="mode"):
    pass


class FutureDateTimeConstraint(FormioStruct, tag="future", tag_field="mode"):
    pass


class PastDateTimeConstraint(FormioStruct, tag="past", tag_field="mode"):
    pass


class DateConstraintDelta(FormioStruct, frozen=True):
    years: int | None = None
    months: int | None = None
    days: int | None = None


class RelativeDateConstraint(
    FormioStruct, kw_only=True, tag="relativeToVariable", tag_field="mode"
):
    variable: Key | None = None
    delta: DateConstraintDelta = DateConstraintDelta()
    operator: Literal["add", "subtract"] = "add"


type DateTimeTranslatableProperties = Literal["label", "description", "tooltip"]


class DateTimeExtensions(BaseOpenFormsExtensions[DateTimeTranslatableProperties]):
    min_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | FutureDateTimeConstraint
        | RelativeDateConstraint
        | None
    ) = None
    max_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | PastDateTimeConstraint
        | RelativeDateConstraint
        | None
    ) = None


type DateTimeValidatorKeys = Literal[
    "required", "minDate", "maxDate", "invalid_datetime"
]


class DateTimeValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []
    # min and max date are specified through the date picker config
    # min_date: datetime | None = None
    # max_date: datetime | None = None


class DateTimePickerConfig(FormioStruct):
    # TODO: should be datetime instead of str, but they're not all valid RFC3339 encoded.
    min_date: str | None = None
    max_date: str | None = None


class DateTime(Component, tag="datetime"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    date_picker: DateTimePickerConfig | None = None
    default_value: datetime | None | Sequence[datetime | None] = None
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[DateTimeValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: DateTimeExtensions | None = None
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[DateTimeValidatorKeys] | None = None
    validate: DateTimeValidate = msgspec.field(default_factory=DateTimeValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> datetime | None | Sequence[datetime | None] | Sentinel:
        match (self.multiple, value):
            case False, datetime():
                return value
            case True, datetime() | None if strict:
                raise ValueError("You must pass a list of values when multiple=True")
            case True, Sequence():
                return [item for item in value if isinstance(item, datetime)]
            case False, Sequence() if strict:
                raise ValueError(
                    "You must pass a datetime default_value when multiple=False"
                )
            case _, None:
                return [] if self.multiple else None
        return unset

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
