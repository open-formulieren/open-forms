"""
Type definitions to be used in type hints for Formio structures.

Formio components are JSON blobs adhering to a formio-specific schema. We define
(subsets) of these schema's to make it easier to reason about the code operating on
(parts of) the schema.
"""

from .base import Component, FormioConfiguration, OptionDict
from .custom import AddressNLComponent, DateComponent
from .vanilla import (
    Column,
    ColumnsComponent,
    ContentComponent,
    DatetimeComponent,
    EditGridComponent,
    FieldsetComponent,
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    TextFieldComponent,
)

__all__ = [
    # base
    "Component",
    "OptionDict",
    "FormioConfiguration",
    # standard
    "TextFieldComponent",
    "DateComponent",
    "DatetimeComponent",
    "FileComponent",
    "SelectComponent",
    "SelectBoxesComponent",
    "RadioComponent",
    # layout
    "ContentComponent",
    "Column",
    "ColumnsComponent",
    "FieldsetComponent",
    # special
    "EditGridComponent",
    "AddressNLComponent",
    # deprecated
]
