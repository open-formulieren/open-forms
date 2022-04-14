from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register


@register("iit-hackathon")
class IITPrefill(BasePlugin):
    verbose_name = _("IIT Hackathon")
    requires_auth = AuthAttribute.bsn

    @staticmethod
    def get_available_attributes() -> list:
        return []

    @classmethod
    def get_prefill_values(
        cls, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if not submission.bsn:
            return {}

        import bpdb

        bpdb.set_trace()
