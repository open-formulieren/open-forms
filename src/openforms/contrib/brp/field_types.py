from typing import Any, Dict, List, Tuple

from rest_framework.request import Request

from openforms.core.custom_field_types import register

from .models import BRPConfig


@register("npFamilyMembers")
def fill_out_family_members(
    component: Dict[str, Any], request: Request
) -> Dict[str, Any]:

    # change the type to a primitive
    component["type"] = "selectboxes"
    component["fieldSet"] = False
    component["inline"] = False
    component["inputType"] = "checkbox"

    # set the available choices
    child_choices = get_np_children(request)

    component["values"] = [
        {
            "label": label,
            "value": value,
        }
        for value, label in child_choices
    ]

    if "mask" in component:
        del component["mask"]

    return component


def get_np_children(request: Request) -> List[Tuple[str, str]]:
    config = BRPConfig.get_solo()
    client = config.get_client()

    bsn = request.session.get("bsn")
    if not bsn:
        raise RuntimeError("No authenticated person!")

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
