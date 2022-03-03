from typing import Any

from ..typing import Component
from .printable import filter_printable
from .registry import register

__all__ = ["format_value", "filter_printable"]


def format_value(info: Component, value: Any, as_html=False):
    return register.format(info, value, as_html=as_html)
