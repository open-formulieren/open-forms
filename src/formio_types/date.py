from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime
from typing import Literal, assert_never

import msgspec
import structlog

from openforms.typing import VariableValue
from stuf.stuf_bg.utils import datetime_in_amsterdam

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Key,
    Prefill,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)


class NoDateConstraint(FormioStruct, tag="", tag_field="mode"):
    pass


class FixedValueDateConstraint(FormioStruct, tag="fixedValue", tag_field="mode"):
    pass


class FutureDateConstraint(FormioStruct, tag="future", tag_field="mode"):
    include_today: bool | None = None


class PastDateConstraint(FormioStruct, tag="past", tag_field="mode"):
    include_today: bool | None = None


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


type DateTranslatableProperties = Literal[
    "label", "description", "tooltip", "placeholder"
]


class DateExtensions(BaseOpenFormsExtensions[DateTranslatableProperties]):
    widget: Literal["inputGroup", "datePicker"] = "datePicker"
    min_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | FutureDateConstraint
        | RelativeDateConstraint
        | None
    ) = None
    max_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | PastDateConstraint
        | RelativeDateConstraint
        | None
    ) = None


type DateValidatorKeys = Literal["required", "minDate", "maxDate", "invalid_date"]


class DateValidate(FormioStruct):
    required: bool = False
    min_date: date | None = None
    max_date: date | None = None


class DatePickerConfig(FormioStruct):
    # FIXME: should be date instances, but we have a mix of date, datetimes and empty
    # strings which msgspec can't handle properly yet. we need to fix the source
    # configuration
    min_date: str | None = None
    max_date: str | None = None


# FIXME: should convert str -> date, but can't do `date | Literal[""] | None` in msgspec
# due to everything being string based and empty string not being parseable as a date.
type DateValue = str


class Date(Component, tag="date"):
    autocomplete: str = ""  # used in appointments
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    date_picker: DatePickerConfig | None = None
    default_value: DateValue | Sequence[DateValue] = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[DateValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: DateExtensions | None = None
    placeholder: str = ""
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[DateValidatorKeys] | None = None
    validate: DateValidate = msgspec.field(default_factory=DateValidate)

    def __post_init__(self):
        # TODO: remove the string types when we have proper date parsing
        match (self.multiple, self.default_value):
            case True, str() | None:
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a date default_value when multiple=False"
                )

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case date() if not self.multiple:
                date_only = (
                    datetime_in_amsterdam(value).date()
                    if isinstance(value, datetime)
                    else value
                )
                self.default_value = date_only.isoformat()
            case Sequence() if self.multiple:
                self.default_value = [
                    (
                        datetime_in_amsterdam(item).date()
                        if isinstance(item, datetime)
                        else item
                    ).isoformat()
                    for item in value
                    if isinstance(item, date)
                ]
            case None if not self.multiple:
                self.default_value = ""
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
        self.placeholder = do_render(self.placeholder)
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
        test_with_trace(self.placeholder, attribute="placeholder")
        test_with_trace(self.tooltip, attribute="tooltip")

        normalized = (
            self.default_value
            if isinstance(self.default_value, Sequence)
            else [self.default_value]
        )
        for _value in normalized:
            test_with_trace(_value, attribute="default_value")
