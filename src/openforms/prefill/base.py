from typing import Any, Container, Iterable

from openforms.authentication.service import AuthAttribute
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.typing import JSONEncodable

from .constants import IdentifierRoles


class AllComponentTypes(Container[str]):
    def __contains__(self, thing):
        # even the ones that don't exist (yet)
        return True


class BasePlugin(AbstractBasePlugin):
    requires_auth: AuthAttribute | None = None
    for_components: Container[str] = AllComponentTypes()

    @staticmethod
    def get_available_attributes(
        reference: dict[str, str] | None = None,
    ) -> Iterable[tuple[str, str]]:
        """
        Return a choice list of available attributes this plugin offers.

        :param reference: a dict based on which we retrieve the available attributes.
          Can be used when we have dynamic lists of attributes.
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
            and submission.auth_info.attribute == cls.requires_auth
        ):
            return submission.auth_info.value
