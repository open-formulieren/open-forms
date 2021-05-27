from typing import Any, Dict, Iterable, List, Tuple

from django.utils.translation import gettext_lazy as _

from ...base import BasePlugin
from ...registry import register
from .constants import Attributes

from openforms.submissions.models import Submission


@register("stufbg")
class StufBgPrefill(BasePlugin):
    verbose_name = _("StUF-BG")

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        return Attributes.choices

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        bsn = submission.bsn

        # TODO get the list of attribute choices
        #   make call to get these values
        # return a dictionary with these values

        return {}
