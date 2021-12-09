from typing import Any, Dict

from rest_framework.request import Request

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.custom_field_types import register
from openforms.submissions.models import Submission

from .constants import FamilyMembersDataAPIChoices
from .handlers.haal_centraal import get_np_children_haal_centraal
from .models import FamilyMembersTypeConfig


@register("npFamilyMembers")
def fill_out_family_members(
    component: Dict[str, Any], request: Request, submission: Submission
) -> Dict[str, Any]:

    # Check authentication details
    form_auth = request.session.get(FORM_AUTH_SESSION_KEY)
    if not form_auth:
        raise RuntimeError("No authenticated person!")

    if form_auth.get("attribute") != AuthAttribute.bsn:
        raise RuntimeError("No BSN found in the authentication details.")

    bsn = form_auth["value"]

    # Decide which API should be used to retrieve the children's data
    config = FamilyMembersTypeConfig.get_solo()
    handlers = {
        FamilyMembersDataAPIChoices.haal_centraal: get_np_children_haal_centraal,
    }

    # Change the component configuration
    component["type"] = "selectboxes"
    component["fieldSet"] = False
    component["inline"] = False
    component["inputType"] = "checkbox"

    if not len(component["values"]) or component["values"][0] == {
        "label": "",
        "value": "",
    }:
        child_choices = handlers[config.data_api](bsn)

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
