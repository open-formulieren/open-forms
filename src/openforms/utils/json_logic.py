"""
Utilities to parse/process jsonLogic expressions.
"""
from dataclasses import dataclass, field
from typing import List, Union

from django.utils.translation import ugettext_lazy as _

from json_logic import operations
from rest_framework import serializers

__all__ = ["JsonLogicTest"]

JSONLogicValue = Union[str, int, "JsonLogicTest"]

# TODO move to json-logic package?
TIME_OPERATORS = ["today", "years", "date"]


@dataclass
class JsonLogicTest:
    operator: str
    values: List[JSONLogicValue] = field(default_factory=list)

    @classmethod
    def from_expression(cls, expression: dict):
        operator = get_operator(expression)
        values = expression[operator]

        # convert unary syntactic sugar to normalized format
        if not isinstance(values, (list, tuple)):
            values = [values]

        normalized = [normalize_value(value) for value in values]
        return cls(
            operator=operator,
            values=normalized,
        )

    @staticmethod
    def is_valid(expression: dict, raise_exception=False) -> bool:
        """
        Check that:
        * The expression is a dictionary with one key
        * All operators present are supported
        * If there are dates present, check that there is no mix&match of dates and non-dates operands
        """
        if not is_logic(expression):
            if raise_exception:
                raise serializers.ValidationError(
                    _("Expression does not look like jsonLogic")
                )
            return False

        if not contains_supported_operators(expression):
            if raise_exception:
                raise serializers.ValidationError(
                    _("Unsupported operator in jsonLogic")
                )
            return False

        if contains_dates(expression):
            # Check that if one operand is a date/today, the other operands should be dates, years or today operators
            if not uses_dates_consistently(expression):
                if raise_exception:
                    raise serializers.ValidationError(
                        _("Mix and match of dates and other types in jsonLogic")
                    )
                return False

        return True


def is_logic(expression) -> bool:
    if not (isinstance(expression, dict) and len(list(expression.keys())) == 1):
        return False
    return True


def get_operator(expression) -> str:
    return list(expression.keys())[0]


def normalize_value(value: Union[dict, list, tuple, int, str]) -> JSONLogicValue:
    if not isinstance(value, (dict, list)):
        return value

    # not sure how correct this is :grimacing:
    if isinstance(value, (list, tuple)):
        return [normalize_value(val) for val in value]

    if isinstance(value, dict):
        return JsonLogicTest.from_expression(value)

    raise NotImplementedError(f"Unknown value type: {type(value)}")


def contains_dates(expression: Union[dict, list, int, str]) -> bool:
    if isinstance(expression, list):
        for expression_item in expression:
            if contains_dates(expression_item):
                return True
        return False
    elif isinstance(expression, dict):
        operator = get_operator(expression)
        if operator in TIME_OPERATORS:
            return True
        else:
            values = expression[operator]
            if isinstance(values, list):
                for value in values:
                    if contains_dates(value):
                        return True
            return False

    return False


def uses_dates_consistently(expression: Union[dict, list, int, str]) -> bool:
    """
    Traverse the JsonLogic expression as a tree. For every operator node, check if it is one of the 'time'
    operators, i.e. "date", "today", "years". If the operator is a 'time operator', stop the search on this branch
    and return True for this node.
    If it is not, then continue to check if the children operator nodes are time operators. Return True for
    this operator node only if all the children operator nodes are 'time operators'.
    """
    contains_date_operands = []
    if not isinstance(expression, (list, dict)):
        return False
    elif isinstance(expression, list):
        for expression_item in expression:
            contains_date_operands.append(uses_dates_consistently(expression_item))
    elif isinstance(expression, dict):
        operator = get_operator(expression)
        if operator in TIME_OPERATORS:
            return True
        else:
            values = expression[operator]
            if isinstance(values, list):
                for value in values:
                    contains_date_operands.append(uses_dates_consistently(value))
            else:
                return False

    return all(contains_date_operands)


def contains_supported_operators(expression: Union[dict, list, int, str]) -> bool:
    if isinstance(expression, dict):
        operator = get_operator(expression)
        if operator not in list(operations.keys()) + ["var", "missing", "missing_some"]:
            return False

        values = expression[operator]
        if not isinstance(values, list):
            values = [values]
        for value in values:
            if not contains_supported_operators(value):
                return False

    if isinstance(expression, list):
        for expression_item in expression:
            if not contains_supported_operators(expression_item):
                return False

    return True
