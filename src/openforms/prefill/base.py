from collections.abc import Collection, Container, Iterable
from typing import Any, TypedDict

from rest_framework import serializers

from openforms.authentication.service import AuthAttribute
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.submissions.models.submission_value_variable import (
    SubmissionValueVariable,
)
from openforms.typing import JSONEncodable, JSONObject
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import IdentifierRoles


class AllComponentTypes(Container[str]):
    def __contains__(self, thing):
        # even the ones that don't exist (yet)
        return True


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


class Options(TypedDict):
    pass


SerializerCls = type[serializers.Serializer]


class BasePlugin[OptionsT: Options](AbstractBasePlugin):
    requires_auth: Collection[AuthAttribute] = ()
    for_components: Container[str] = AllComponentTypes()
    options: SerializerCls = EmptyOptions

    @staticmethod
    def get_available_attributes() -> Iterable[tuple[str, str]]:
        """
        Return a choice list of available attributes this plugin offers.
        """
        raise NotImplementedError(
            "You must implement the 'get_available_attributes' method."
        )

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, JSONEncodable]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        :param identifier_role: A string with one of the choices in :class:`IdentifierRoles`
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.

        When no prefill value can be found for a given attribute, you may omit the key
        altogether, or use ``None``.
        """
        raise NotImplementedError("You must implement the 'get_prefill_values' method.")

    def verify_initial_data_ownership(
        self, submission: Submission, prefill_options: OptionsT
    ) -> None:
        """
        Hook to check if the authenticated user is the owner of the object
        referenced to by `initial_data_reference`

        If any error occurs in this check, it should raise a `PermissionDenied`

        :param submission: an active :class:`Submission` instance
        :param prefill_options: the configuration options, after validation and
          deserialization through the :attr:`options` serializer class.
        """
        raise NotImplementedError(
            "You must implement the 'verify_initial_data_ownership' method."
        )

    @classmethod
    def get_prefill_values_from_options(
        cls,
        submission: Submission,
        options: OptionsT,
        submission_value_variable: SubmissionValueVariable,
    ) -> dict[str, JSONEncodable]:
        """
        Given the saved form variable, which contains the prefill_options, look up the appropriate
        values and return them.

        :param submission: an active :class:`Submission` instance, which can supply
          the required initial data reference to fetch the correct prefill values.
        :param options: contains plugin-specific configuration options.
        :param submission_value_variable: the submission value variable which is needed
          in some prefill plugins.
        :return: a mapping where the keys are form variable keys, and the values are the
          initial/default values to assign to the matching form variable. The variable keys
          can point to both component and user defined variables.
        """
        raise NotImplementedError(
            "You must implement the 'get_prefill_values_from_options' method."
        )

    @classmethod
    def get_co_sign_values(
        cls, submission: Submission, identifier: str
    ) -> tuple[dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the pre-fill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        raise NotImplementedError("You must implement the 'get_co_sign_values' method.")

    @classmethod
    def get_identifier_value(
        cls, submission: Submission, identifier_role: IdentifierRoles
    ) -> str | None:
        """
        Given a submission and the role of the identifier, return the value of the identifier.

        The role of the identifier has to do with whether it is the 'main' identifier or an identifier
        of someone logging in on behalf of someone/something else.

        :param submission: an active :class:`Submission` instance
        :param identifier_role: A string with one of the choices in :class:`IdentifierRoles`
        :return: The value for the identifier
        """
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and cls.requires_auth
            and submission.auth_info.attribute in cls.requires_auth
        ):
            return submission.auth_info.value

    @classmethod
    def configuration_context(cls) -> JSONObject | None:
        return None
