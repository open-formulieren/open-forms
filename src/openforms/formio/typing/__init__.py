"""
Type definitions to be used in type hints for Formio structures.

Formio components are JSON blobs adhering to a formio-specific schema. We define
(subsets) of these schema's to make it easier to reason about the code operating on
(parts of) the schema.
"""

from .base import Component, OptionDict
from .custom import CosignComponent, DateComponent
from .vanilla import (
    Column,
    ColumnsComponent,
    ContentComponent,
    DatetimeComponent,
    FileComponent,
    RadioComponent,
)

__all__ = [
    "Component",
    "OptionDict",
    "ContentComponent",
    "FileComponent",
    "RadioComponent",
    "Column",
    "ColumnsComponent",
    "DatetimeComponent",
    "CosignComponent",
    "DateComponent",
]
