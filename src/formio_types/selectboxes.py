from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping, Sequence
from typing import Annotated, Literal, assert_never

import msgspec
import structlog
from msgspec import Meta

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
type SelectboxesValidatorKeys = Literal[
    "required", "minSelectedCount", "maxSelectedCount"
]

type SelectboxesTranslatableProperties = Literal["label", "description", "tooltip"]


class SelectboxesExtensions(BaseOpenFormsExtensions[SelectboxesTranslatableProperties]):
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


class SelectboxesValidate(FormioStruct):
    required: bool = False
    min_selected_count: Annotated[int, Meta(ge=1)] | None = None
    max_selected_count: Annotated[int, Meta(ge=1)] | None = None


class Selectboxes(Component, tag="selectboxes"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: Mapping[str, bool] = {}
    description: str = ""
    errors: Errors[SelectboxesValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: SelectboxesExtensions = msgspec.field(
        default_factory=SelectboxesExtensions
    )
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SelectboxesValidatorKeys] | None = None
    validate: SelectboxesValidate = msgspec.field(default_factory=SelectboxesValidate)
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
                        f"Select {self.key} manual values will be ignored.",
                        category=DeprecationWarning,
                        stacklevel=1,
                    )
                    # do not clear, as they may be assigned by dynamic evaluation on a
                    # dict that's then passed to msgspec
                    # self.values = []
            case _:
                assert_never(self.open_forms.data_src)

        if not self.default_value and self.values:
            self.default_value = {
                option.value: False for option in self.values if option.value
            }

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("selectboxes does not support prefill")

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
