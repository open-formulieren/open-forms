from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

from rest_framework import serializers

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission

T = TypeVar("T")
"""A type variable representing the type of the value being validated by the plugin."""


class StringValueSerializer(serializers.Serializer):
    """A default serializer that accepts ``value`` as a string."""

    value = serializers.CharField()


class BasePlugin(ABC, AbstractBasePlugin, Generic[T]):

    value_serializer: ClassVar[type[serializers.BaseSerializer]] = StringValueSerializer
    """The serializer to be used to validate the value."""

    for_components: ClassVar[tuple[str, ...]] = tuple()
    """The components that can make use of this validator."""

    @property
    def is_enabled(self) -> bool:
        # TODO always enabled for now, see: https://github.com/open-formulieren/open-forms/issues/1149
        return True

    @abstractmethod
    def __call__(self, value: T, submission: Submission) -> bool:
        pass
