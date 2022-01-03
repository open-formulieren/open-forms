from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Type

from rest_framework import serializers

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.utils.mixins import JsonSchemaSerializerMixin

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission

SerializerCls = Type[serializers.Serializer]


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class BasePlugin(ABC, AbstractBasePlugin):
    configuration_options: SerializerCls = EmptyOptions
    """
    A serializer class describing the plugin-specific configuration options.

    A plugin instance is the combination of a plugin callback and a set of options that
    are plugin specific. Multiple forms can use the same plugin with different
    configuration options. Using a serializer allows us to serialize the options as JSON
    in the database, and de-serialize them into native Python/Django objects when the
    plugin is called.
    """
    camel_case_ignore_fields = None
    """
    Iterable of JSON keys to ignore when converting between snake_case/camelCase.
    """

    @abstractmethod
    def register_submission(
        self, submission: "Submission", options: dict
    ) -> Optional[dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_reference_from_result(self, result: Any) -> str:
        """
        Extract the public submission reference from the result data.

        This method must return a string to be saved on the submission model.

        :arg result: the raw underlying JSONField datastructure.
        """
        raise NotImplementedError()

    def update_payment_status(self, submission: "Submission", options: dict):
        raise NotImplementedError()
