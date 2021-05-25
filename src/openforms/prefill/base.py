from typing import Any, Dict, Iterable, List, Tuple

from openforms.submissions.models import Submission


class BasePlugin:
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
        """
        raise NotImplementedError("You must implement the 'get_prefill_values' method.")
