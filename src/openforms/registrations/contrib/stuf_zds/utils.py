from json_logic.typing import Primitive


def _flatten_data(flattened_data: dict[str, Primitive], data: dict, path: str) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            updated_path = f"{path}.{key}" if path else key
            _flatten_data(flattened_data, value, updated_path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            updated_path = f"{path}.{index}" if path else index
            _flatten_data(flattened_data, value, updated_path)
    else:
        flattened_data[path] = data


def flatten_data(data) -> dict[str, Primitive]:
    """
    Flatten any nested data

    For example, if data is ``{"variableKey": ["value1", {"key1": "value2"}]``, this will return
    ``{"variableKey.0": "value1", "variableKey.1.key1": "value2"}``.
    """
    flattened_data = {}
    _flatten_data(flattened_data, data, "")
    return flattened_data
