from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _

import requests

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...registry import register

# https://github.com/sgort/Test_data_hackathon_Den_Haag/blob/main/Testgevallen_IIT_v1.json

SOURCE = "https://raw.githubusercontent.com/sgort/Test_data_hackathon_Den_Haag/main/Testgevallen_IIT_v1.json"


@register("iit-hackathon")
class IITPrefill(BasePlugin):
    verbose_name = _("IIT Hackathon")
    requires_auth = AuthAttribute.bsn

    @staticmethod
    def get_available_attributes() -> list:
        data = requests.get(SOURCE).json()
        keys = data[0].keys()
        return [(key, key) for key in keys]

    @classmethod
    def get_prefill_values(
        cls, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if not submission.bsn:
            return {}

        import bpdb

        bpdb.set_trace()
