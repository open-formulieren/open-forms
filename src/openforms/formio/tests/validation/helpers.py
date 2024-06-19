from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

from rest_framework.exceptions import ErrorDetail
from rest_framework.utils.serializer_helpers import ReturnDict

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONValue
from openforms.validations.registry import Registry

from ...service import build_serializer
from ...typing import Component


def validate_formio_data(
    component: Component, data: JSONValue, extra_context: dict[str, Any] = {}
) -> tuple[bool, ReturnDict]:
    """
    Dynamically build the serializer, validate it and return the status.
    """

    context = {"submission": SubmissionFactory.build(), **extra_context}
    serializer = build_serializer(components=[component], data=data, context=context)
    is_valid = serializer.is_valid(raise_exception=False)
    return is_valid, serializer.errors


def extract_error(errors: ReturnDict, key: str, index: int = 0) -> ErrorDetail:
    return errors[key][index]


@contextmanager
def replace_validators_registry():
    new_register = Registry()
    with patch("openforms.validations.drf_validators.register", new=new_register):
        yield new_register
