import logging
from typing import Any, Dict, Iterable, List, Tuple

from django.utils.translation import gettext_lazy as _

import xmltodict
from glom import T as Target, glom

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission
from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS, FieldChoices
from stuf.stuf_bg.models import StufBGConfig

from ...base import BasePlugin
from ...registry import register

logger = logging.getLogger(__name__)

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
    requires_auth = AuthAttribute.bsn

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
        except KeyError as exc:
            logger.error(
                "Response data has an unexpected shape",
                extra={"response": dict_response},
                exc_info=exc,
            )
            return {}

        response_dict = {}
        for attribute in attributes:
            value = glom(data, ATTRIBUTES_TO_STUF_BG_MAPPING[attribute], default=None)
            if "@noValue" not in value:
                response_dict[attribute] = value

        return response_dict

    def test_config(self):
        config = StufBGConfig.get_solo()

        if not config.service:
            return ['Geen service gedefinieerd voor STUF BAG client (endpoint for StUF-ZDS from the clien)']

        client = config.service
        # print('bag client', client)
        # print('password not hash', config._state.fields_cache['service'].__dict__)
        # print('stuf bag', config._state.fields_cache['service'])
        print('get client', dir(config.get_client().service))
        return True
