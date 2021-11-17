import re
from typing import Any, Union

from djangorestframework_camel_case.util import (
    camelize_re,
    underscore_to_camel as _underscore_to_camel,
)
from rest_framework.serializers import Serializer


def underscore_to_camel(input_: Union[str, int]) -> str:
    """
    Convert a string from under_score to camelCase.
    """
    if not isinstance(input_, str):
        return input_

    return re.sub(camelize_re, _underscore_to_camel, input_)


def get_from_serializer_data_or_instance(
    field: str, data: dict, serializer: Serializer
) -> Any:
    data_value = data.get(field)
    if data_value:
        return data_value

    instance = serializer.instance
    if not instance:
        return None

    serializer_field = serializer.fields[field]
    return serializer_field.get_attribute(instance)
