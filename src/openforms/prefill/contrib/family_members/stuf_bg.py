from typing import assert_never

from stuf.stuf_bg.client import get_client as get_stufbg_client
from stuf.stuf_bg.data import NaturalPersonDetails

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMemberOptions


def get_data_from_stuf_bg(
    bsn: str, options: FamilyMemberOptions
) -> list[NaturalPersonDetails]:
    with get_stufbg_client() as client:
        match options["type"]:
            case FamilyMembersTypeChoices.partners:
                return client.get_partners_or_children(
                    bsn,
                    "inp.heeftAlsEchtgenootPartner",
                    "partners",
                )

            case FamilyMembersTypeChoices.children:
                include_deceased = options["include_deceased"]
                children = client.get_partners_or_children(
                    bsn,
                    "inp.heeftAlsKinderen",
                    "children",
                    include_deceased=include_deceased,
                )

                min_age = options["min_age"]
                max_age = options["max_age"]

                children = [
                    child
                    for child in filter_members_by_age(
                        children, min_age=min_age, max_age=max_age
                    )
                    if (
                        include_deceased
                        or (not include_deceased and not child.deceased)
                    )
                ]

                return children
            case _:  # pragma: no cover
                assert_never(options["type"])
