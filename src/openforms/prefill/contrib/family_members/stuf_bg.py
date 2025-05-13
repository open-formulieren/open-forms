from collections import defaultdict

from stuf.stuf_bg.client import get_client as get_stufbg_client
from stuf.stuf_bg.data import NaturalPersonDetails

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMembersChildOptions, FamilyMembersPartnerOptions
from .utils import convert_to_json_serializable


def get_data_from_stuf_bg(
    bsn: str,
    options: FamilyMembersPartnerOptions | FamilyMembersChildOptions,
) -> dict[str, list[NaturalPersonDetails]]:
    results: defaultdict[str, list[NaturalPersonDetails]] = defaultdict(list)

    with get_stufbg_client() as client:
        match options["type"]:
            case FamilyMembersTypeChoices.partners:
                partners_list = client.get_partners_or_children(
                    bsn, "inp.heeftAlsEchtgenootPartner", "partners"
                )
                results[options["type"]] = partners_list
                return convert_to_json_serializable(results)
            case FamilyMembersTypeChoices.children:
                include_deceased = options.get("include_deceased", True)

                children_list = client.get_partners_or_children(
                    bsn,
                    "inp.heeftAlsKinderen",
                    "children",
                    include_deceased=(
                        include_deceased if include_deceased is not None else True
                    ),
                )

                min_age = options.get("min_age")
                max_age = options.get("max_age")

                # no filters needed
                if not (min_age or max_age or (not include_deceased)):
                    results[options["type"]] = children_list
                    return convert_to_json_serializable(results)

                if include_deceased is False:
                    children_list = [
                        child for child in children_list if not child.deceased
                    ]

                filtered_results = filter_members_by_age(
                    children_list, min_age=min_age, max_age=max_age
                )

                results[options["type"]] = filtered_results
                return convert_to_json_serializable(results)
