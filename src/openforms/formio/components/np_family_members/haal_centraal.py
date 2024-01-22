from openforms.contrib.haal_centraal.clients import get_brp_client
from openforms.contrib.haal_centraal.clients.brp import Person
from openforms.submissions.models import Submission


def get_np_family_members_haal_centraal(
    bsn: str,
    include_children: bool,
    include_partners: bool,
    submission: Submission | None = None,
) -> list[tuple[str, str]]:
    # TODO: add tests for missing configuration and error handling!
    with get_brp_client(submission) as client:
        family_data = client.get_family_members(bsn, include_children, include_partners)

    family_member_choices = [
        (family_member.bsn, get_np_name(family_member))
        for family_member in family_data
        if bsn
    ]
    return family_member_choices


def get_np_name(person: Person) -> str:
    bits = [
        person.name.voornamen,
        person.name.voorvoegsel,
        person.name.geslachtsnaam,
    ]
    relevant_bits = [bit for bit in bits if bit]
    return " ".join(relevant_bits).strip()
