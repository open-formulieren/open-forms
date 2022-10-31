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
    attribute = form_auth["attribute"]

    assert (
        attribute in AuthAttribute.values
    ), f"Unexpected auth attribute {attribute} specified"

    AuthInfo.objects.update_or_create(submission=submission, defaults=form_auth)
