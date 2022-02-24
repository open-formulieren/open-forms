from typing import Any

from ..typing import Component
from .printable import filter_printable
from .registry import register

__all__ = ["format_value", "filter_printable"]


def format_value(info: Component, value: Any):
    return register.format(info, value)
