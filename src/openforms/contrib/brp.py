from typing import Any, Dict

from rest_framework.request import Request

from .handlers import register

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

    print("saw custom component")

    return component
