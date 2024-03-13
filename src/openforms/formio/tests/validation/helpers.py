from rest_framework.utils.serializer_helpers import ReturnDict

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONValue

from ...service import build_serializer
from ...typing import Component


def validate_formio_data(
    component: Component, data: JSONValue
) -> tuple[bool, ReturnDict]:
    """
    Dynamically build the serializer, validate it and return the status.
    """
    context = {"submission": SubmissionFactory.build()}
    serializer = build_serializer(components=[component], data=data, context=context)
    is_valid = serializer.is_valid(raise_exception=False)
    return is_valid, serializer.errors


def extract_error(errors: ReturnDict, key: str, index: int = 0):
    return errors[key][index]
