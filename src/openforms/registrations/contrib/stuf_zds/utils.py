from collections.abc import Collection, Sequence
from datetime import date, datetime, time
from typing import Any

from openforms.typing import JSONPrimitive


def _flatten_data_and_convert_to_primitives(
    flattened_data: dict[str, JSONPrimitive],
    data: Any,
    *,
    path: str = "",
    keys_to_csv_serialize: Collection[str] = (),
) -> None:
    match data:
        case dict():
            for key, value in data.items():
                # For the root mapping, test if the keys need to be CSV serialized instead of
                # flattened recursively
                if (
                    path == ""
                    and key in keys_to_csv_serialize
                    and isinstance(value, Sequence)
                ):
                    flattened_data[key] = _csv_serialize_data(value)
                else:
                    updated_path = f"{path}.{key}" if path else key
                    _flatten_data_and_convert_to_primitives(
                        flattened_data, value, path=updated_path
                    )
        case list():
            for index, value in enumerate(data):
                updated_path = f"{path}.{index}" if path else str(index)
                _flatten_data_and_convert_to_primitives(
                    flattened_data, value, path=updated_path
                )
        case date() | time() | datetime():
            flattened_data[path] = data.isoformat()
        case _:
            flattened_data[path] = data


def _csv_serialize_data(value: Sequence[object]) -> str:
    flattened_data = {}
    for index, item in enumerate(value):
        _flatten_data_and_convert_to_primitives(flattened_data, item, path=str(index))
    # Note that this assumes no nested dicts that contain comma's, so with weird input
    # data you'll get weird output...
    return ",".join(str(item) for item in flattened_data.values())


def flatten_data_and_convert_to_primitives(
    data: Any,
    *,
    keys_to_csv_serialize: Collection[str] = (),
) -> dict[str, JSONPrimitive]:
    """
    Flatten any nested data, and convert to JSON primitives.

    For example:
    >>> data = {"variableKey": ["value1", {"key1": date(2025, 11, 18)}]}
    >>> flattened_data = flatten_data_and_convert_to_primitives(data)
    >>> print(flattened_data)
    {"variableKey.0": "value1", "variableKey.1.key1": "2025-11-18"}
    """
    flattened_data = {}
    _flatten_data_and_convert_to_primitives(
        flattened_data,
        data,
        keys_to_csv_serialize=keys_to_csv_serialize,
    )
    return flattened_data
