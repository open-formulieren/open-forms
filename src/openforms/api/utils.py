import re
from typing import Any, Union

from djangorestframework_camel_case.util import (
    camelize_re,
    underscore_to_camel as _underscore_to_camel,
)
from drf_spectacular.utils import extend_schema, extend_schema_serializer
from rest_framework.serializers import Serializer
from rest_framework.views import APIView


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


def mark_experimental(func_or_class):
    if issubclass(func_or_class, Serializer):
        extend_fn = extend_schema_serializer
    elif issubclass(func_or_class, APIView):
        extend_fn = extend_schema
    else:
        raise NotImplementedError(f"Type {type(func_or_class)} is not supported yet.")
    decorator = extend_fn(extensions={"x-experimental": True})
    return decorator(func_or_class)
