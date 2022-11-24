from typing import List, Tuple

from stuf.stuf_bg.models import StufBGConfig


def get_np_children_stuf_bg(bsn: str) -> List[Tuple[str, str]]:
    config = StufBGConfig.get_solo()
    client = config.get_client()

    attributes = [
        "inp.heeftAlsKinderen",
    ]

    data = client.get_values(bsn, attributes)

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
