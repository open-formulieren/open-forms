from typing import Any, Dict

from openforms.authentication.constants import AuthAttribute
from openforms.formio.typing import Component
from openforms.forms.custom_field_types import register
from openforms.submissions.models import Submission

from .constants import FamilyMembersDataAPIChoices
from .handlers.haal_centraal import get_np_children_haal_centraal
from .handlers.stuf_bg import get_np_children_stuf_bg
from .models import FamilyMembersTypeConfig


@register("npFamilyMembers")
def fill_out_family_members(
    component: Component, submission: Submission
) -> Dict[str, Any]:

    # Check authentication details
    if not submission.is_authenticated:
        raise RuntimeError("No authenticated person!")

    if submission.auth_info.attribute != AuthAttribute.bsn:
        raise RuntimeError("No BSN found in the authentication details.")

    bsn = submission.auth_info.value

    # Decide which API should be used to retrieve the children's data
    config = FamilyMembersTypeConfig.get_solo()
    handlers = {
        FamilyMembersDataAPIChoices.haal_centraal: get_np_children_haal_centraal,
        FamilyMembersDataAPIChoices.stuf_bg: get_np_children_stuf_bg,
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
