from __future__ import annotations

import warnings
from collections.abc import Collection, Iterator, Mapping, Sequence
from typing import ClassVar, Literal, assert_never

import msgspec

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Option,
    Registration,
    TemplatableValue,
    TranslatedErrors,
)

# FIXME: should be Literal["required"], but there is garbage data
type RadioValidatorKeys = str

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
    default_value: str | None = None
    description: str = ""
    errors: Errors[RadioValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: RadioExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[RadioValidatorKeys] | None = None
    validate: RadioValidate | None = None
    values: Sequence[Option] = []
    """
    Either manually provided or set from variable/reference list.
    """

    SUPPORTED_TEMPLATE_ATTRIBUTES: ClassVar[Collection[str]] = frozenset(
        ("label", "description", "tooltip", "default_value")
    )

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

    def iter_template_attributes(self) -> Iterator[tuple[str, TemplatableValue]]:
        yield from super().iter_template_attributes()
        # FIXME: this does not support mutation yet, only parsing/validation
        yield ("values", msgspec.to_builtins(self.values))
