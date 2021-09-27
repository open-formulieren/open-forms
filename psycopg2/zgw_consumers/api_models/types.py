from typing import Dict, List, Union

JSONPrimitive = Union[str, int, None, float]
JSONValue = Union[JSONPrimitive, "JSONObject", List["JSONValue"]]
JSONObject = Dict[str, JSONValue]
