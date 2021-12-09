from typing import List, Tuple

from openforms.contrib.brp.models import BRPConfig


def get_np_children_haal_centraal(bsn: str) -> List[Tuple[str, str]]:
    config = BRPConfig.get_solo()
    client = config.get_client()

    # actual operation ID from standard! but Open Personen has the wrong one
    # operation_id = "ingeschrevenpersonenBurgerservicenummerkinderen"
    operation_id = "ingeschrevenpersonen_kinderen_list"
    # path = client.get_operation_url(operation_id, burgerservicenummer=bsn)
    path = client.get_operation_url(
        operation_id, ingeschrevenpersonen_burgerservicenummer=bsn
    )

    response_data = client.request(path=path, operation=operation_id)
    children = response_data["_embedded"]["kinderen"]

    child_choices = [
        (child["burgerservicenummer"], get_np_name(child)) for child in children
    ]
    return child_choices


def get_np_name(natuurlijk_persoon: dict) -> str:
    embedded = natuurlijk_persoon["_embedded"]["naam"]
    bits = [
        embedded.get("voornamen", ""),
        embedded.get("voorvoegsel", ""),
        embedded.get("geslachtsnaam", ""),
    ]
    relevant_bits = [bit for bit in bits if bit]
    return " ".join(relevant_bits).strip()
