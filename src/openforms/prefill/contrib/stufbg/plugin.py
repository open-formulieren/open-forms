import logging
from typing import Any, Dict, Iterable, List, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import xmltodict
from defusedxml.lxml import fromstring as df_fromstring
from glom import T as Target, glom
from lxml import etree
from requests import HTTPError, RequestException

from openforms.authentication.constants import AuthAttribute
from openforms.plugins.exceptions import InvalidPluginConfiguration
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
    FieldChoices.voorvoegselGeslachtsnaam: Target["voorvoegselGeslachtsnaam"],
    FieldChoices.straatnaam: Target["verblijfsadres"]["gor.straatnaam"],
    FieldChoices.huisnummer: Target["verblijfsadres"]["aoa.huisnummer"],
    FieldChoices.huisletter: Target["verblijfsadres"]["aoa.huisletter"],
    FieldChoices.huisnummertoevoeging: Target["verblijfsadres"][
        "aoa.huisnummertoevoeging"
    ],
    FieldChoices.postcode: Target["verblijfsadres"]["aoa.postcode"],
    FieldChoices.woonplaatsNaam: Target["verblijfsadres"]["wpl.woonplaatsNaam"],
    FieldChoices.gemeenteVanInschrijving: Target["inp.gemeenteVanInschrijving"],
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
        except (TypeError, KeyError) as exc:
            try:
                # Get the fault information if there
                fault = dict_response["Envelope"]["Body"]["Fault"]
            except KeyError:
                fault = {}
            finally:
                logger.error(
                    "Response data has an unexpected shape",
                    extra={"response": dict_response, "fault": fault},
                    exc_info=exc,
                )
                return {}

        response_dict = {}
        for attribute in attributes:
            value = glom(data, ATTRIBUTES_TO_STUF_BG_MAPPING[attribute], default=None)

            if value and "@noValue" not in value:
                response_dict[attribute] = value

        return response_dict

    def check_config(self):
        check_bsn = "111222333"

        config = StufBGConfig.get_solo()
        if not config.service:
            raise InvalidPluginConfiguration(_("Service not selected"))

        client = config.get_client()
        try:
            data = client.get_request_data(check_bsn, [FieldChoices.bsn])
            response = client.make_request(data)
            response.raise_for_status()
        except (RequestException, HTTPError) as e:
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=e)
            )
        else:
            try:
                xml = df_fromstring(response.content)
            except etree.XMLSyntaxError as e:
                raise InvalidPluginConfiguration(
                    _("SyntaxError in response: {exception}").format(exception=e)
                )
            else:
                faults = xml.xpath("//*[local-name()='Fault']/faultstring")
                if not faults or faults[0].text != "Object niet gevonden":
                    raise InvalidPluginConfiguration(
                        _(
                            "Unexpected response: expected '{message}' SOAP response"
                        ).format(message="Object niet gevonden")
                    )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:stuf_bg_stufbgconfig_change",
                    args=(StufBGConfig.singleton_instance_id,),
                ),
            ),
        ]
