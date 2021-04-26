from typing import Any, Dict, List, Tuple

from rest_framework.request import Request

from openforms.forms.custom_field_types import register
from openforms.submissions.models import Submission

from .models import BRPConfig


@register("map")
def pdok_map(
    component: Dict[str, Any], request: Request, submission: Submission
) -> Dict[str, Any]:

    # change the type to a primitive
    component["type"] = "charfield"
    component["fieldSet"] = False
    component["inline"] = False

    if "mask" in component:
        del component["mask"]

    return component
