from openforms.contrib.haal_centraal.constants import (
    NaturalPersonDetails as HC_NaturalPersonDetails,
)
from stuf.stuf_bg.constants import NaturalPersonDetails as StUFBG_NaturalPersonDetails


def filter_members_by_age(
    results: list[HC_NaturalPersonDetails | StUFBG_NaturalPersonDetails],
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[HC_NaturalPersonDetails | StUFBG_NaturalPersonDetails]:
    min_age = min_age or 0
    max_age = max_age or 500

    age_filtered = [
        member
        for member in results
        if member.age is not None and min_age <= member.age <= max_age
    ]

    return age_filtered
