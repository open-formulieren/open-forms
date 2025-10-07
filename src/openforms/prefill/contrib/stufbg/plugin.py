from collections.abc import Collection
from typing import Any

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from glom import T as Target, glom

from openforms.authentication.service import AuthAttribute
from openforms.submissions.models import Submission
from stuf.stuf_bg.checks import check_config as check_stuf_bg_config
from stuf.stuf_bg.client import get_client
from stuf.stuf_bg.constants import FieldChoices
from stuf.stuf_bg.models import StufBGConfig

from ...base import BasePlugin
from ...constants import IdentifierRoles
from ...exceptions import PrefillSkipped
from ...registry import register

logger = structlog.stdlib.get_logger(__name__)


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
    FieldChoices.voorletters: Target["voorletters"],
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
    FieldChoices.adresBuitenland1: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland1"
    ],
    FieldChoices.adresBuitenland2: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland2"
    ],
    FieldChoices.adresBuitenland3: Target["sub.verblijfBuitenland"][
        "sub.adresBuitenland3"
    ],
}


@register("stufbg")
class StufBgPrefill(BasePlugin):
    verbose_name = _("StUF-BG")
    requires_auth = (AuthAttribute.bsn,)

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        return FieldChoices.choices

    @staticmethod
    def _get_values_for_bsn(bsn: str, attributes: Collection[str]) -> dict[str, Any]:
        with get_client() as client:
            data = client.get_values(bsn, [str(attr) for attr in attributes])

        response_dict = {}
        for attribute in attributes:
            value = glom(
                data,
                ATTRIBUTES_TO_STUF_BG_MAPPING[FieldChoices(attribute)],
                default=None,
            )
            # if the XML element has attributes, we don't get a return value of the content,
            # but rather an OrderedDict from xmltodict with the #text key for the content
            # and @<attribute> keys for the attributes.
            # E.g. <ns:geboortedatum StUF:indOnvolledigeDatum="M">19600701</ns:geboortedatum>,
            # see #1617 for such a regression.
            if isinstance(value, dict) and "#text" in value:
                value = value["#text"]

            if value and "@noValue" not in value:
                response_dict[attribute] = value

        # postcodes in StUF BG responses have this form "[1-9][0-9]{3}[A-Z]{0,2}"
        # Our prefill tests expect roughly "[1-9][0-9]{3} [A-Z]{0,2}"
        if FieldChoices.postcode in response_dict and " " not in (
            postcode := response_dict[FieldChoices.postcode]
        ):
            response_dict[FieldChoices.postcode] = postcode[:4] + " " + postcode[4:]

        return response_dict

    @classmethod
    def get_identifier_value(
        cls, submission: Submission, identifier_role: IdentifierRoles
    ) -> str | None:
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and cls.requires_auth
            and submission.auth_info.attribute in cls.requires_auth
        ):
            return submission.auth_info.value

        if identifier_role == IdentifierRoles.authorizee:
            auth_context = submission.auth_info.to_auth_context_data()
            # check if we have new-style authentication context capturing, and favour
            # that over the legacy format
            legal_subject = auth_context["authorizee"]["legalSubject"]
            # this only works if the identifier is a BSN
            if (
                "representee" not in auth_context
                or legal_subject["identifierType"] != "bsn"
            ):
                return None
            return legal_subject["identifier"]

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRoles = IdentifierRoles.main,
    ) -> dict[str, Any]:
        if not (bsn_value := cls.get_identifier_value(submission, identifier_role)):
            #  If there is no bsn we can't prefill any values so just return
            logger.info(
                "lookup_identifier_absent",
                submission_uuid=str(submission.uuid),
                plugin=cls,
            )
            raise PrefillSkipped("Missing BSN.")

        return cls._get_values_for_bsn(bsn_value, attributes)

    @classmethod
    def get_co_sign_values(
        cls, submission: Submission, identifier: str
    ) -> tuple[dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identfier: the unique co-signer identifier used to look up the details
          in the pre-fill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        values = cls._get_values_for_bsn(
            identifier,
            [
                FieldChoices.voornamen,
                FieldChoices.voorvoegselGeslachtsnaam,
                FieldChoices.geslachtsnaam,
            ],
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
        check_stuf_bg_config()

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
