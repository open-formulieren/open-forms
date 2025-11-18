from abc import ABC, abstractmethod
from typing import ClassVar

from rest_framework import serializers

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.typing import JSONValue


class StringValueSerializer(serializers.Serializer):
    """A default serializer that accepts ``value`` as a string."""

    value = serializers.CharField()


class BasePlugin[T: JSONValue](ABC, AbstractBasePlugin):
    """The base class for validation plugins.

    This class is generic over the type of the validated value, defaulting to ``str``.
    """

    value_serializer: ClassVar[type[serializers.BaseSerializer]] = StringValueSerializer
    """The serializer to be used to validate the value."""

    for_components: ClassVar[tuple[str, ...]] = tuple()
    """The components that can make use of this validator."""

    @property
    def is_enabled(self) -> bool:
        # TODO always enabled for now, see: https://github.com/open-formulieren/open-forms/issues/1149
        return True

    @abstractmethod
    def __call__(self, value: T, submission: Submission) -> None:
        """
        Raise a django or DRF validation error for invalid values.
        """
        pass
