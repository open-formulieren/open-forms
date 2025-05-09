from collections import defaultdict

from stuf.stuf_bg.client import get_client as get_stufbg_client
from stuf.stuf_bg.constants import NaturalPersonDetails

from .constants import FamilyMembersTypeChoices
from .filters import filter_members_by_age
from .typing import FamilyMembersChildOptions, FamilyMembersPartnerOptions
from .utils import covert_to_json_serializable


def get_data_from_stuf_bg(
    bsn: str, options: FamilyMembersPartnerOptions | FamilyMembersChildOptions
) -> dict[str, dict[str, list[NaturalPersonDetails]]]:
    variable_key = options["form_variable"]
    results: defaultdict[str, dict[str, list[NaturalPersonDetails]]] = defaultdict(dict)

    with get_stufbg_client() as client:
        if options["type"] == FamilyMembersTypeChoices.partners:
            results[variable_key]["partners"] = client.get_partners_or_children(
                bsn, "inp.heeftAlsEchtgenootPartner", "partners"
            )
        elif options["type"] == FamilyMembersTypeChoices.children:
            results[variable_key]["children"] = client.get_partners_or_children(
                bsn, "inp.heeftAlsKinderen", "children"
            )

            min_age = options.get("min_age")
            max_age = options.get("max_age")
            include_deceased = options.get("include_deceased")

            # no filters needed
            if not (min_age or max_age or (not include_deceased)):
                serializable_data = covert_to_json_serializable(results)
                return serializable_data

            children_list = results[variable_key]["children"]

            if include_deceased is False:
                children_list = [child for child in children_list if not child.deceased]

            if not (min_age or max_age):
                results[variable_key]["children"] = children_list
                serializable_data = covert_to_json_serializable(results)
                return serializable_data

            results[variable_key]["children"] = filter_members_by_age(
                children_list, min_age=min_age, max_age=max_age
            )

    serializable_data = covert_to_json_serializable(results)

    return serializable_data
