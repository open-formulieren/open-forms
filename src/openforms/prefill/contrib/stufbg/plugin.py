from typing import Any, Dict, Iterable, List, Tuple

from django.utils.translation import gettext_lazy as _

import xmltodict

from openforms.submissions.models import Submission
from stuf.stuf_bg.constants import (
    NAMESPACE_REPLACEMENTS,
    Attributes,
    attributes_to_stuf_bg_mapping,
)
from stuf.stuf_bg.models import StufBGConfig

from ...base import BasePlugin
from ...registry import register


@register("stufbg")
class StufBgPrefill(BasePlugin):
    verbose_name = _("StUF-BG")

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        return Attributes.choices

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if submission.bsn is None:
            #  If there is no bsn we can't prefill any values so just return
            return {}

        config = StufBGConfig.get_solo()
        client = config.get_client()
        response_data = client.get_data_for_attributes(submission.bsn, attributes)

        dict_response = xmltodict.parse(
            response_data,
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )

        try:
            address = dict_response["Envelope"]["Body"]["npsLa01"]["antwoord"][
                "object"
            ]["verblijfsadres"]
        except KeyError:
            # TODO Do we want to throw our own exception here?  This should never happen
            address = {}

        response_dict = {}

        for attribute in attributes:
            response_dict[attribute] = address.get(
                attributes_to_stuf_bg_mapping[attribute]
            )

        return response_dict
