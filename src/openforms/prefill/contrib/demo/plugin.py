import random
from functools import partial
from typing import Any

from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from openforms.config.data import Action
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...registry import register
from .constants import Attributes

CALLBACKS = {
    Attributes.random_number.value: lambda: random.randint(1000, 10_000),
    Attributes.random_string.value: partial(get_random_string, length=10),
}


@register("demo")
class DemoPrefill(BasePlugin):
    verbose_name = _("Demo")
    is_demo_plugin = True

    @staticmethod
    def get_available_attributes():
        return Attributes.choices

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, Any]:
        """
        Given the requested attributes, look up the appropriate values and return them.

        :param submission: an active :class:`Submission` instance, which can be supply
          the required context to fetch the correct prefill values.
        :param attributes: a list of requested prefill attributes, provided in bulk
          to efficiently fetch as much data as possible with the minimal amount of calls.
        """
        return {attr: CALLBACKS[attr]() for attr in attributes}

    def check_config(self) -> list[Action]:
        """
        Demo config is always valid.
        """
        return []
