import xmltodict

from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS
from stuf.stuf_bg.models import StufBGConfig


# TODO Should be reworked to only retrieve and return the requested attributes
#  conforming to the interface of openforms.prefill.base.BasePlugin.get_prefill_values
def get_person_address(bsn: str):
    config = StufBGConfig.get_solo()
    client = config.get_client()
    response_data = client.get_address(bsn)

    dict_response = xmltodict.parse(
        response_data,
        process_namespaces=True,
        namespaces=NAMESPACE_REPLACEMENTS,
    )

    try:
        address = dict_response["Envelope"]["Body"]["npsLa01"]["antwoord"]["object"][
            "verblijfsadres"
        ]
    except KeyError:
        # TODO Do we want to throw our own exception here?  This should never happen
        address = {}

    return {
        "street_name": address.get("gor.straatnaam"),
        "house_number": address.get("aoa.huisnummer"),
        "house_letter": address.get("aoa.huisletter"),
        "house_letter_addition": address.get("aoa.huisnummertoevoeging"),
        "postcode": address.get("aoa.postcode"),
        "city": address.get("wpl.woonplaatsNaam"),
    }
