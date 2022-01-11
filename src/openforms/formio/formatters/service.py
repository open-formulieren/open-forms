from typing import Any, Dict

from .registry import register


def format_value(info: Dict, value: Any):
    return register.format(info, value)
