from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rest_framework import serializers

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.utils.mixins import JsonSchemaSerializerMixin

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

SerializerCls = type[serializers.Serializer]


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


@dataclass
class PreRegistrationResult:
    """Encapsulate the submission reference and any intermediate result from pre-registration."""

    reference: str = ""
    data: dict | None = None


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
    ) -> dict | None:
        raise NotImplementedError()

    def update_payment_status(self, submission: "Submission", options: dict):
        raise NotImplementedError()

    def pre_register_submission(
        self, submission: "Submission", options: dict
    ) -> PreRegistrationResult:
        """Perform any tasks before registering the submission

        For plugins where the registration backend does not generate a reference number,
        no need to implement this method.
        """
        return PreRegistrationResult()

    def get_custom_templatetags_libraries(self) -> list[str]:
        """
        Return a list of custom templatetags libraries that will be added to the 'sandboxed' Django templates backend.
        """
        return []
