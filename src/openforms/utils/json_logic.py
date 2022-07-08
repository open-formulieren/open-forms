"""
Utilities to parse/process jsonLogic expressions.
"""
from dataclasses import dataclass, field
from typing import List, Union

from json_logic import jsonLogic

__all__ = ["JsonLogicTest"]

JSONLogicValue = Union[str, int, "JsonLogicTest"]


@dataclass
class JsonLogicTest:
    operator: str
    values: List[JSONLogicValue] = field(default_factory=list)

    @classmethod
    def from_expression(cls, expression: dict):
        try:
            jsonLogic(expression)
        except ValueError as exc:
            raise ValueError("Invalid jsonLogic expression given") from exc

        operator = list(expression.keys())[0]
        values = expression[operator]

        # convert unary syntactic sugar to normalized format
        if not isinstance(values, (list, tuple)):
            values = [values]

        normalized = [normalize_value(value) for value in values]
        return cls(
            operator=operator,
            values=normalized,
        )


def normalize_value(value: Union[dict, list, tuple, int, str]) -> JSONLogicValue:
    if not isinstance(value, (dict, list)):
        return value

    # not sure how correct this is :grimacing:
    if isinstance(value, (list, tuple)):
        return [normalize_value(val) for val in value]

    if isinstance(value, dict):
        return JsonLogicTest.from_expression(value)

    raise NotImplementedError(f"Unknown value type: {type(value)}")
