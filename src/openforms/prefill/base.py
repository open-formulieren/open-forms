from typing import Any, Dict, Iterable, List, Tuple

from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission


class BasePlugin:
    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    requires_auth = None

    """
    Specify the human-readable label for the plugin.
    """

    def __init__(self, identifier: str):
        self.identifier = identifier

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        """
        Return a choice list of available attributes this plugin offers.
        """
        raise NotImplementedError(
            "You must implement the 'get_available_attributes' method."
        )

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.

        When no pre-fill value can be found for a given attribute, you may omit the key
        altogether, or use ``None``.
        """
        raise NotImplementedError("You must implement the 'get_prefill_values' method.")
