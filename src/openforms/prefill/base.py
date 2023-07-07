from typing import Any, Dict, Iterable, List, Optional, Tuple

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission


class BasePlugin(AbstractBasePlugin):
    requires_auth = None

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        """
        Return a choice list of available attributes this plugin offers.
        """
        raise NotImplementedError(  # pragma: nocover
            "You must implement the 'get_available_attributes' method."
        )

    def get_prefill_values(
        self,
        submission: Submission,
        attributes: List[str],
        identifier_role: str = "main",
    ) -> Dict[str, Any]:
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
        raise NotImplementedError(
            "You must implement the 'get_prefill_values' method."
        )  # pragma: nocover

    def get_co_sign_values(
        self, identifier: str, submission: Optional["Submission"] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the pre-fill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        raise NotImplementedError(
            "You must implement the 'get_co_sign_values' method."
        )  # pragma: nocover

    def get_identifier_value(
        self, submission: Submission, identifier_role: str
    ) -> str | None:
        """
        Given a submission and the role of the identifier, return the value of the identifier.

        The role of the identifier has to do with whether it is the 'main' identifier or an identifier
        of someone logging in on behalf of someone/something else.

        :param submission: an active :class:`Submission` instance
        :param identifier_role: A string with one of the choices in :class:`IdentifierRoles`
        :return: The value for the identifier
        """
        raise NotImplementedError(
            "You must implement the 'get_identifier_value' method."
        )  # pragma: nocover
