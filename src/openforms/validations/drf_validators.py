"""
Utilities to work with a DRF validator (field-level) for a given validation plugin.

.. todo:: use type hints from drf-stubs when we add those to base dependencies.
"""

from collections.abc import Iterable

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

    def __init__(self, plugins: Iterable[str]):
        assert all(
            plugin in register for plugin in plugins
        ), "Invalid plugin identifier specified"
        self.plugins = plugins

    # FIXME: after deserializing the input data, this may actually be any python type,
    # so the JSONValue type hint is not accurate.
    def __call__(self, value: JSONValue, field: serializers.Field) -> None:
        """
        Validate that the data conforms to at least one of the specified plugins.

        Validation plugins on our Formio components operate on an OR-basis rather than
        AND - the input is considered valid as soon as one of the validators treats
        it as valid.
        """
        submission = field.context.get("submission", None)
        assert isinstance(
            submission, Submission
        ), "You must pass the submission in the serializer context"

        # evaluate all plugins to collect the error messages in case none is valid
        messages: list[str] = []
        for plugin in self.plugins:
            result = register.validate(plugin, value=value, submission=submission)
            # as soon as one is valid -> abort, there are no validation messages to
            # display
            if result.is_valid:
                return
            messages += result.messages

        raise serializers.ValidationError(messages, code="invalid")
