from typing import Any, Dict

from .printable import filter_printable
from .registry import register

__all__ = ["format_value", "filter_printable"]


def format_value(info: Dict, value: Any):
    return register.format(info, value)
