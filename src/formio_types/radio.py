from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping, Sequence
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
    Option,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)

type RadioValidatorKeys = Literal["required"]

type RadioTranslatableProperties = Literal["label", "description", "tooltip"]


class RadioExtensions(BaseOpenFormsExtensions[RadioTranslatableProperties]):
    data_src: Literal["manual", "variable", "referenceLists"] = "manual"
    # for variable
    items_expression: str | Mapping[str, object] | Sequence[Sequence[str]] = ""
    # for reference lists
    service: str = ""
    code: str = ""

    def __post_init__(self):
        match self.data_src:
            case "manual":
                pass
            case "variable":
                if not self.items_expression:
                    raise ValueError("You must provide an items expression.")
            case "referenceLists":
                # we'd rather hard fail here, but existing code handles this gracefully,
                # so for now we warn.
                if not (self.service and self.code):
                    warnings.warn(
                        "Service and list references are required.",
                        category=DeprecationWarning,
                        stacklevel=1,
                    )
            case _:
                assert_never(self.data_src)


class RadioValidate(FormioStruct):
    required: bool = False


class Radio(Component, tag="radio"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str = ""
    description: str = ""
    errors: Errors[RadioValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: RadioExtensions = msgspec.field(default_factory=RadioExtensions)
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[RadioValidatorKeys] | None = None
    validate: RadioValidate = msgspec.field(default_factory=RadioValidate)
    values: Sequence[Option] = []
    """
    Either manually provided or set from variable/reference list.
    """

    def __post_init__(self):
        match self.open_forms.data_src:
            case "manual":
                pass
            case "variable" | "referenceLists":
                if self.values:
                    warnings.warn(
                        f"Radio {self.key} manual values will be ignored.",
                        category=DeprecationWarning,
                        stacklevel=1,
                    )
                    # do not clear, as they may be assigned by dynamic evaluation on a
                    # dict that's then passed to msgspec
                    # self.values = []
            case _:
                assert_never(self.open_forms.data_src)

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case str():
                self.default_value = value
            case None:
                self.default_value = ""
            case _:
                logger.warning(
                    "received_invalid_default_value",
                    component=str(type(self)),
                    value=value,
                )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

        for option in self.values:
            option.label = do_render(option.label)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")

        for option in self.values:
            test_with_trace(option.label, attribute="values")
