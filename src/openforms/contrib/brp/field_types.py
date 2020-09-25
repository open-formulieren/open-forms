from typing import Any, Dict

from rest_framework.request import Request

from openforms.core.custom_field_types import register

BSN_CHOICES = (
    ("534135286", "shea"),
    ("462447546", "bart"),
    ("407174205", "anna"),
    ("462677448", "sven"),
    ("005255545", "sergei"),
)


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
    component["values"] = [
        {
            "label": label,
            "value": value,
        }
        for value, label in BSN_CHOICES
    ]

    if "mask" in component:
        del component["mask"]

    return component
