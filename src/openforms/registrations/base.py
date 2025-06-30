from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypedDict, TypeVar

from rest_framework import serializers

from openforms.formio.typing import Component
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import JSONObject
from openforms.utils.mixins import JsonSchemaSerializerMixin

if TYPE_CHECKING:
    from openforms.forms.models import FormVariable
    from openforms.submissions.models import Submission


SerializerCls = type[serializers.Serializer]


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


@dataclass
class PreRegistrationResult:
    """Encapsulate the submission reference and any intermediate result from pre-registration."""

    reference: str = ""
    data: dict | None = None


class Options(TypedDict):
    pass


OptionsT = TypeVar("OptionsT", bound=Options)


class BasePlugin(Generic[OptionsT], ABC, AbstractBasePlugin):
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
        self, submission: Submission, options: OptionsT
    ) -> dict | None:
        raise NotImplementedError()

    def update_payment_status(
        self, submission: Submission, options: OptionsT
    ) -> dict | None:
        raise NotImplementedError()

    def verify_initial_data_ownership(
        self, submission: Submission, options: OptionsT
    ) -> None:
        """
        Check that the submission user is the owner of the registration target.

        Registration backends can possibly update existing objects, which are
        referenced through :attr:`submission.initial_data_reference`. These plugins
        must check that the submission user is actually the 'owner' of this object. For
        example, a permit request may have a BSN stored, or a case can have an
        initiator/authorizee identified by a BSN/Chamber of Commerce number.

        :param submission: an active :class:`Submission` instance.
        :param options: the deserialized plugin configuration options.
        """
        raise NotImplementedError(
            "You must implement the 'verify_initial_data_ownership' method."
        )

    def pre_register_submission(
        self, submission: Submission, options: OptionsT
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

    def get_variables(self) -> list[FormVariable]:
        """
        Return the static variables for this registration plugin.
        """
        return []

    def update_registration_with_confirmation_email(
        self, submission: Submission, options: OptionsT
    ) -> dict | None:
        """Update the registered submission with a confirmation email.

        Should be overridden by subclasses.
        """
        return None

    def process_variable_schema(
        self, component: Component, schema: JSONObject, options: OptionsT
    ):
        """Process a variable schema for this registration plugin."""
        raise NotImplementedError()

    @staticmethod
    def allows_json_schema_generation(options: OptionsT) -> bool:
        """Indicate whether the plugin allows generating a JSON schema."""
        return False
