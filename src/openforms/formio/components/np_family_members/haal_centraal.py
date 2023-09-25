from typing import List, Tuple

from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.clients.brp import Person


def get_np_children_haal_centraal(bsn: str) -> List[Tuple[str, str]]:
    # TODO: add tests for missing configuration and error handling!
    with get_brp_client() as client:
        children_data = client.get_children(bsn)

    child_choices = [(child.bsn, get_np_name(child)) for child in children_data if bsn]
    return child_choices


def get_np_name(person: Person) -> str:
    bits = [
        person.name.voornamen,
        person.name.voorvoegsel,
        person.name.geslachtsnaam,
    ]
    relevant_bits = [bit for bit in bits if bit]
    return " ".join(relevant_bits).strip()
