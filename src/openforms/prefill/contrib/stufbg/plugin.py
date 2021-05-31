from typing import Any, Dict, Iterable, List, Tuple

from django.utils.translation import gettext_lazy as _

import xmltodict
from glom import T as Target, glom

from openforms.submissions.models import Submission
from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS, FieldChoices
from stuf.stuf_bg.models import StufBGConfig

from ...base import BasePlugin
from ...registry import register

ATTRIBUTES_TO_STUF_BG_MAPPING = {
    FieldChoices.bsn: Target["inp.bsn"],
    FieldChoices.voornamen: Target["voornamen"],
    FieldChoices.geslachtsnaam: Target["geslachtsnaam"],
    FieldChoices.straatnaam: Target["verblijfsadres"]["gor.straatnaam"],
    FieldChoices.huisnummer: Target["verblijfsadres"]["aoa.huisnummer"],
    FieldChoices.huisletter: Target["verblijfsadres"]["aoa.huisletter"],
    FieldChoices.huisnummertoevoeging: Target["verblijfsadres"][
        "aoa.huisnummertoevoeging"
    ],
    FieldChoices.postcode: Target["verblijfsadres"]["aoa.postcode"],
    FieldChoices.woonplaatsNaam: Target["verblijfsadres"]["wpl.woonplaatsNaam"],
}


@register("stufbg")
class StufBgPrefill(BasePlugin):
    verbose_name = _("StUF-BG")

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        return FieldChoices.choices

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if not submission.bsn:
            #  If there is no bsn we can't prefill any values so just return
            return {}

        config = StufBGConfig.get_solo()
        client = config.get_client()
        response_data = client.get_values_for_attributes(submission.bsn, attributes)

        dict_response = xmltodict.parse(
            response_data,
            process_namespaces=True,
            namespaces=NAMESPACE_REPLACEMENTS,
        )

        try:
            data = dict_response["Envelope"]["Body"]["npsLa01"]["antwoord"]["object"]
        except KeyError:
            # TODO Do we want to throw our own exception here?  This should never happen
            data = {}

        response_dict = {}
        for attribute in attributes:
            response_dict[attribute] = glom(
                data, ATTRIBUTES_TO_STUF_BG_MAPPING[attribute], default=None
            )

        return response_dict
