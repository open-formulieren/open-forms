"""
Utilities to work with a DRF validator (field-level) for a given validation plugin.

.. todo:: use type hints from drf-stubs when we add those to base dependencies.
"""

from rest_framework import serializers

from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from .registry import register


class PluginValidator:
    """
    DRF-compatible validator which wraps the registry validator plugins.

    Note that the submission instance must be passed in the serializer context which
    uses this validator.
    """

    requires_context = True

    def __init__(self, plugin: str):
        assert plugin in register, "Invalid plugin identifier specified"
        self.plugin = plugin

    # FIXME: after deserializing the input data, this may actually be any python type,
    # so the JSONValue type hint is not accurate.
    def __call__(self, value: JSONValue, field: serializers.Field) -> None:
        submission = field.context.get("submission", None)
        assert isinstance(
            submission, Submission
        ), "You must pass the submission in the serializer context"
        result = register.validate(self.plugin, value=value, submission=submission)
        if result.is_valid:
            return
        raise serializers.ValidationError(result.messages, code="invalid")
