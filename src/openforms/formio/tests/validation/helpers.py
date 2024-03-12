from rest_framework.utils.serializer_helpers import ReturnDict

from openforms.typing import JSONValue

from ...service import build_serializer
from ...typing import Component


def validate_formio_data(
    component: Component, data: JSONValue
) -> tuple[bool, ReturnDict]:
    """
    Dynamically build the serializer, validate it and return the status.
    """
    serializer = build_serializer(components=[component], data=data)
    is_valid = serializer.is_valid(raise_exception=False)
    return is_valid, serializer.errors


def extract_error(errors: ReturnDict, key: str, index: int = 0):
    return errors[key][index]
