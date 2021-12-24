import logging
from typing import Any, Dict, Iterable, List, Tuple

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from defusedxml.lxml import fromstring as df_fromstring
from glom import T as Target, glom
from lxml import etree
from requests import HTTPError, RequestException

from openforms.authentication.constants import AuthAttribute
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.models import Submission
from stuf.stuf_bg.constants import FieldChoices
from stuf.stuf_bg.models import StufBGConfig

from ...base import BasePlugin
from ...registry import register

logger = logging.getLogger(__name__)


"""
    # original
    Bsn
    Voornamen
    VoorvoegselGeslachtsnaam
    Geslachtsnaam
    Straatnaam
    Huisnummer
    Huisletter
    HuisnummerToevoeging
    Postcode
    Woonplaatsnaam

    # added
    Geboorteplaats
    Geslachtsaanduiding
    Geboortedatum
    Geboorteland
    DatumOverlijden

    # not in bg0310
    # AanduidingBijHuisnummer


    LandAdresBuitenland
    Regel1AdresBuitenland
    Regel2AdresBuitenland
    Regel3AdresBuitenland

"""

"""
plenty of examples for responses can be found in open-personen:
https://github.com/maykinmedia/open-personen/tree/master/src/openpersonen/templates/response
"""

ATTRIBUTES_TO_STUF_BG_MAPPING = {
    FieldChoices.bsn: Target["inp.bsn"],
    FieldChoices.voornamen: Target["voornamen"],
    FieldChoices.geslachtsnaam: Target["geslachtsnaam"],
    FieldChoices.voorvoegselGeslachtsnaam: Target["voorvoegselGeslachtsnaam"],
    FieldChoices.geboorteplaats: Target["inp.geboorteplaats"],
    FieldChoices.geslachtsaanduiding: Target["geslachtsaanduiding"],
    FieldChoices.geboortedatum: Target["geboortedatum"],
    FieldChoices.geboorteland: Target["inp.geboorteLand"],
    FieldChoices.overlijdensdatum: Target["overlijdensdatum"],
    FieldChoices.straatnaam: Target["verblijfsadres"]["gor.straatnaam"],
    FieldChoices.huisnummer: Target["verblijfsadres"]["aoa.huisnummer"],
    FieldChoices.huisletter: Target["verblijfsadres"]["aoa.huisletter"],
    FieldChoices.huisnummertoevoeging: Target["verblijfsadres"][
        "aoa.huisnummertoevoeging"
    ],
    FieldChoices.postcode: Target["verblijfsadres"]["aoa.postcode"],
    FieldChoices.woonplaatsNaam: Target["verblijfsadres"]["wpl.woonplaatsNaam"],
    FieldChoices.gemeenteVanInschrijving: Target["inp.gemeenteVanInschrijving"],
    FieldChoices.landAdresBuitenland: Target["sub.verblijfBuitenland"]["lnd.landnaam"],
    FieldChoices.regel1AdresBuitenland: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland1"
    ],
    FieldChoices.regel2AdresBuitenland: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland2"
    ],
    FieldChoices.regel3AdresBuitenland: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland3"
    ],
}


@register("stufbg")
class StufBgPrefill(BasePlugin):
    verbose_name = _("StUF-BG")
    requires_auth = AuthAttribute.bsn

    def get_available_attributes(self) -> Iterable[Tuple[str, str]]:
        return FieldChoices.choices

    def _get_values_for_bsn(
        self, bsn: str, attributes: Iterable[str]
    ) -> Dict[str, Any]:
        config = StufBGConfig.get_solo()
        client = config.get_client()

        data = client.get_values(bsn, attributes)

        response_dict = {}
        for attribute in attributes:
            value = glom(data, ATTRIBUTES_TO_STUF_BG_MAPPING[attribute], default=None)

            if value and "@noValue" not in value:
                response_dict[attribute] = value

        return response_dict

    def get_prefill_values(
        self, submission: Submission, attributes: List[str]
    ) -> Dict[str, Any]:
        if not submission.bsn:
            #  If there is no bsn we can't prefill any values so just return
            return {}

        return self._get_values_for_bsn(submission.bsn, attributes)

    def get_co_sign_values(self, identifier: str) -> Tuple[Dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identfier: the unique co-signer identifier used to look up the details
          in the pre-fill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        values = self._get_values_for_bsn(
            identifier,
            (
                FieldChoices.voornamen,
                FieldChoices.voorvoegselGeslachtsnaam,
                FieldChoices.geslachtsnaam,
            ),
        )
        representation_bits = [
            " ".join(
                [f"{name[0]}." for name in values[FieldChoices.voornamen].split(" ")]
            ),
            values.get(FieldChoices.voorvoegselGeslachtsnaam, ""),
            values[FieldChoices.geslachtsnaam],
        ]
        return (
            values,
            " ".join([bit for bit in representation_bits if bit]),
        )

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
