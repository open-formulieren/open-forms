from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime
from typing import Literal, override

import msgspec
from of_datetime_utils import datetime_in_amsterdam

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
    TranslatedErrors,
)
from ..templating import TestWithTrace
from ..typing import ComponentValue


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
    variable: Key | msgspec.UnsetType = msgspec.UNSET
    delta: DateConstraintDelta = DateConstraintDelta()
    operator: Literal["add", "subtract"] = "add"


type DateTranslatableProperties = Literal["label", "description", "tooltip"]


class DateExtensions(BaseOpenFormsExtensions[DateTranslatableProperties]):
    widget: Literal["inputGroup", "datePicker"] = "datePicker"
    min_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | FutureDateConstraint
        | RelativeDateConstraint
        | msgspec.UnsetType
    ) = msgspec.UNSET
    max_date: (
        NoDateConstraint
        | FixedValueDateConstraint
        | PastDateConstraint
        | RelativeDateConstraint
        | msgspec.UnsetType
    ) = msgspec.UNSET


type DateValidatorKeys = Literal["required", "minDate", "maxDate", "invalid_date"]


class DateValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []
    # min and max date are specified through the date picker config
    # min_date: date | None = None
    # max_date: date | None = None


class DatePickerConfig(FormioStruct):
    # FIXME: should be date instances, but we have a mix of date, datetimes and empty
    # strings which msgspec can't handle properly yet. we need to fix the source
    # configuration
    min_date: str | None = None
    max_date: str | None = None


class Date(Component, tag="date"):
    # # used in appointments, but not yet used by builder / renderer
    # autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    date_picker: DatePickerConfig | msgspec.UnsetType = msgspec.UNSET
    default_value: date | None | Sequence[date | None] = None
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[DateValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: DateExtensions | msgspec.UnsetType = msgspec.UNSET
    prefill: Prefill | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[DateValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: DateValidate = msgspec.field(default_factory=DateValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> date | None | Sequence[date | None] | msgspec.UnsetType:
        match (self.multiple, value):
            case False, date() | datetime():
                return (
                    datetime_in_amsterdam(value).date()
                    if isinstance(value, datetime)
                    else value
                )
            case True, date() | None if strict:
                raise ValueError("You must pass a list of values when multiple=True")
            case True, Sequence():
                return [
                    (
                        datetime_in_amsterdam(item).date()
                        if isinstance(item, datetime)
                        else item
                    )
                    for item in value
                    if isinstance(item, date)
                ]
            case False, Sequence() if strict:
                raise ValueError(
                    "You must pass a date default_value when multiple=False"
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
