"""
Type definitions to be used in type hints for Formio structures.

Formio components are JSON blobs adhering to a formio-specific schema. We define
(subsets) of these schema's to make it easier to reason about the code operating on
(parts of) the schema.
"""

from .base import Component, OptionDict
from .custom import DateComponent
from .vanilla import (
    BSNComponent,
    CheckboxComponent,
    Column,
    ColumnsComponent,
    ContentComponent,
    CurrencyComponent,
    DatetimeComponent,
    EditGridComponent,
    FileComponent,
    MapComponent,
    PostcodeComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    SignatureComponent,
    TextAreaComponent,
    TextFieldComponent,
    TimeComponent,
)

__all__ = [
    # base
    "Component",
    "OptionDict",
    # standard
    "TextFieldComponent",
    "TextAreaComponent",
    "DateComponent",
    "DatetimeComponent",
    "FileComponent",
    "SelectComponent",
    "SelectBoxesComponent",
    "RadioComponent",
    "PostcodeComponent",
    "TimeComponent",
    "BSNComponent",
    "CurrencyComponent",
    "CheckboxComponent",
    "SignatureComponent",
    "MapComponent",
    # layout
    "ContentComponent",
    "Column",
    "ColumnsComponent",
    # special
    "EditGridComponent",
    # deprecated
]
