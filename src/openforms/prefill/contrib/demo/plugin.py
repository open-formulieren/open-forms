import random
from typing import Any, Dict, List

from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes

CALLBACKS = {
    Attributes.random_number: lambda: random.randint(1000, 10_000),
    Attributes.random_string: get_random_string,
}


@register("demo")
class DemoPrefill(BasePlugin):
    verbose_name = _("Demo")
    is_demo_plugin = True

    @staticmethod
    def get_available_attributes():
        return Attributes.choices

    @staticmethod
    def get_prefill_values(
        submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        """
        return {attr: CALLBACKS[attr]() for attr in attributes}

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
