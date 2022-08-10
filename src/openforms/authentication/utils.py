from typing import Literal, Optional, TypedDict

from openforms.submissions.models import Submission

from .constants import AuthAttribute
from .models import AuthInfo


class FormAuth(TypedDict):
    plugin: str
    attribute: Literal[
        AuthAttribute.bsn,
        AuthAttribute.kvk,
        AuthAttribute.pseudo,
    ]
    value: str
    machtigen: Optional[dict]


def store_auth_details(submission: Submission, form_auth: FormAuth) -> None:
    plugin = form_auth["plugin"]
    attribute = form_auth["attribute"]

    assert (
        attribute in AuthAttribute.values
    ), f"Unexpected auth attribute {attribute} specified"

    if hasattr(submission, "auth_info"):
        # DO NOT log this in plain text, it is considered sensitive information (BSN for example)
        auth_info = submission.auth_info
        auth_info.plugin = plugin
        auth_info.attribute = attribute
        auth_info.value = form_auth["value"]
        auth_info.save()
        return

    auth_data = AuthInfo(
        plugin=plugin,
        attribute=attribute,
        value=form_auth["value"],
        submission=submission,
    )
    auth_data.save()
