from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Literal, assert_never

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

# FIXME: should be Literal["required"], but there is garbage data
type RadioValidatorKeys = str


class RadioExtensions(
    BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]],
):
    data_src: Literal["manual", "variable", "referenceLists"] = "manual"
    # for variable
    items_expression: str | Mapping[str, object] = ""
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
                if not (self.service and self.code):
                    raise ValueError("Service and list references are required.")
            case _:
                assert_never(self.data_src)


class RadioValidate(FormioStruct):
    required: bool = False


class Radio(Component, tag="radio"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | None = None
    description: str = ""
    errors: Errors[RadioValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: RadioExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[RadioValidatorKeys] | None = None
    validate: RadioValidate | None = None
    values: Sequence[Option] = []
    """
    Either manually provided or set from variable/reference list.
    """

    def __post_init__(self):
        if self.open_forms is None:
            self.open_forms = RadioExtensions(data_src="manual")

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
