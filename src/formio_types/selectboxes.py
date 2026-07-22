from __future__ import annotations

import warnings
from collections.abc import Collection, Mapping, Sequence
from typing import Annotated, ClassVar, Literal, assert_never

import msgspec
from msgspec import Meta

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Option,
    Registration,
    TranslatedErrors,
)

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
    default_value: Mapping[str, bool] | None = None
    description: str = ""
    errors: Errors[SelectboxesValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: SelectboxesExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SelectboxesValidatorKeys] | None = None
    validate: SelectboxesValidate | None = None
    values: Sequence[Option] = []
    """
    Either manually provided or set from variable/reference list.
    """

    SUPPORTED_TEMPLATE_ATTRIBUTES: ClassVar[Collection[str]] = frozenset(
        ("label", "description", "tooltip", "default_value")
    )

    def __post_init__(self):
        if self.open_forms is None:
            self.open_forms = SelectboxesExtensions(data_src="manual")

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
