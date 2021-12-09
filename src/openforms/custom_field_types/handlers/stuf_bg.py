from typing import List, Tuple

import xmltodict

from stuf.stuf_bg.constants import NAMESPACE_REPLACEMENTS
from stuf.stuf_bg.models import StufBGConfig


# TODO: Refactor to avoid code duplication with openforms/prefill/contrib/stufbg/plugin.py
def get_np_children_stuf_bg(bsn: str) -> List[Tuple[str, str]]:
    config = StufBGConfig.get_solo()
    client = config.get_client()

    attributes = [
        "inp.heeftAlsKinderen",
    ]

    response_data = client.get_values_for_attributes(bsn, attributes)

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
            return {}

    # Kids
    child_choices = []
    children = data.get("inp.heeftAlsKinderen", [])
    for child in children:
        child_data = child.get("gerelateerde", {})
        bsn = child_data.get("inp.bsn")
        if not bsn:
            continue
        name = get_np_name(child_data)

        child_choices.append((bsn, name))

    return child_choices


def get_np_name(child_data: dict) -> str:
    bits = [
        child_data.get("voornamen", ""),
        child_data.get("voorvoegselGeslachtsnaam", ""),
        child_data.get("geslachtsnaam", ""),
    ]
    relevant_bits = [bit for bit in bits if bit]
    return " ".join(relevant_bits).strip()
