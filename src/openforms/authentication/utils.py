from typing import Literal, Optional, TypedDict

from openforms.submissions.models import Submission

from .constants import AuthAttribute


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

    # DO NOT log this in plain text, it is considered sensitive information (BSN for example)
    identifier = form_auth["value"]
    submission.auth_plugin = plugin
    setattr(submission, attribute, identifier)
    submission.save(update_fields=["auth_plugin", attribute])
