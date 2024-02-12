from openforms.submissions.models import Submission
from stuf.stuf_bg.client import get_client


def get_np_family_members_stuf_bg(
    bsn: str,
    include_children: bool,
    include_partners: bool,
    submission: Submission | None = None,
) -> list[tuple[str, str]]:
    attributes: list[str] = []
    if include_children:
        attributes.append("inp.heeftAlsKinderen")

    if include_partners:
        attributes.append("inp.heeftAlsEchtgenootPartner")

    with get_client() as client:
        data = client.get_values(bsn, attributes)

    # Kids
    family_members = []
    if include_children:
        family_members += data.get("inp.heeftAlsKinderen", [])
    if include_partners:
        family_members += data.get("inp.heeftAlsEchtgenootPartner", [])

    family_member_choices = []
    for family_member in family_members:
        family_member_data = family_member.get("gerelateerde", {})
        bsn = family_member_data.get("inp.bsn")
        if not bsn:
            continue

        name = get_np_name(family_member_data)
        family_member_choices.append((bsn, name))

    return family_member_choices


def get_np_name(person_data: dict) -> str:
    bits = [
        person_data.get("voornamen", ""),
        person_data.get("voorvoegselGeslachtsnaam", ""),
        person_data.get("geslachtsnaam", ""),
    ]
    relevant_bits = [bit for bit in bits if bit]
    return " ".join(relevant_bits).strip()
