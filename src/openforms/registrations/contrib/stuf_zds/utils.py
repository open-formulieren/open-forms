from datetime import date, datetime, time
from typing import Any

from openforms.typing import JSONPrimitive


def _flatten_data_and_convert_to_primitives(
    flattened_data: dict[str, JSONPrimitive], data: Any, path: str
) -> None:
    match data:
        case dict():
            for key, value in data.items():
                updated_path = f"{path}.{key}" if path else key
                _flatten_data_and_convert_to_primitives(
                    flattened_data, value, updated_path
                )
        case list():
            for index, value in enumerate(data):
                updated_path = f"{path}.{index}" if path else index
                _flatten_data_and_convert_to_primitives(
                    flattened_data, value, updated_path
                )
        case date() | time() | datetime():
            flattened_data[path] = data.isoformat()
        case _:
            flattened_data[path] = data


def flatten_data_and_convert_to_primitives(data) -> dict[str, JSONPrimitive]:
    """
    Flatten any nested data, and convert to JSON primitives.

    For example:
    >>> data = {"variableKey": ["value1", {"key1": date(2025, 11, 18)}]}
    >>> flattened_data = flatten_data_and_convert_to_primitives(data)
    >>> print(flattened_data)
    {"variableKey.0": "value1", "variableKey.1.key1": "2025-11-18"}
    """
    flattened_data = {}
    _flatten_data_and_convert_to_primitives(flattened_data, data, "")
    return flattened_data
