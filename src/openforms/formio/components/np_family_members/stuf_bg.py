from typing import List, Tuple

from stuf.stuf_bg.client import get_client


def get_np_children_stuf_bg(bsn: str) -> List[Tuple[str, str]]:
    with get_client() as client:
        data = client.get_values(bsn, ["inp.heeftAlsKinderen"])

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
