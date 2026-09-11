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
# FIXME: should be Literal["required"], but there is garbage data
type SelectValidatorKeys = str

type SelectTranslatableProperties = Literal["label", "description", "tooltip"]


class SelectExtensions(BaseOpenFormsExtensions[SelectTranslatableProperties]):
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


class SelectValidate(FormioStruct):
    required: bool = False


class SelectData(FormioStruct):
    values: Sequence[Option] = []
    """
    Either manually provided or set from variable/reference list.
    """


class Select(Component, tag="select"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    data: SelectData
    data_src: Literal["values"] = "values"
    data_type: Literal["string"] = "string"
    default_value: str | Sequence[str] = ""
    description: str = ""
    errors: Errors[SelectValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: SelectExtensions = msgspec.field(default_factory=SelectExtensions)
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SelectValidatorKeys] | None = None
    validate: SelectValidate = msgspec.field(default_factory=SelectValidate)

    def __post_init__(self):
        match self.open_forms.data_src:
            case "manual":
                pass
            case "variable" | "referenceLists":
                if self.data.values:
                    warnings.warn(
                        f"Select {self.key} manual values will be ignored.",
                        category=DeprecationWarning,
                        stacklevel=1,
                    )
                    # do not clear, as they may be assigned by dynamic evaluation on a
                    # dict that's then passed to msgspec
                    # self.data.values = []
            case _:
                assert_never(self.open_forms.data_src)

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
            case str() if not self.multiple:
                self.default_value = value
            case Sequence() if self.multiple:
                string_values = [x for x in value if isinstance(x, str)]
                self.default_value = string_values
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

        for option in self.data.values:
            option.label = do_render(option.label)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")

        for option in self.data.values:
            test_with_trace(option.label, attribute="values")
