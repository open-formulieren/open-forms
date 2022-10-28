from typing import Literal, Optional, TypedDict

from openforms.submissions.models import Submission

from .constants import AuthAttribute
from .models import AuthInfo, RegistratorInfo


class BaseAuth(TypedDict):
    plugin: str
    attribute: Literal[
        AuthAttribute.bsn,
        AuthAttribute.kvk,
        AuthAttribute.pseudo,
        AuthAttribute.employee_id,
    ]
    value: str


class FormAuth(BaseAuth):
    machtigen: Optional[dict]
    access_token: Optional[str]


def store_auth_details(submission: Submission, form_auth: FormAuth) -> None:
    attribute = form_auth["attribute"]

    assert (
        attribute in AuthAttribute.values
    ), f"Unexpected auth attribute {attribute} specified"

    AuthInfo.objects.update_or_create(submission=submission, defaults=form_auth)


def store_registrator_details(
    submission: Submission, registrator_auth: BaseAuth
) -> None:
    attribute = registrator_auth["attribute"]

    assert (
        attribute in AuthAttribute.values
    ), f"Unexpected auth attribute {attribute} specified"

    RegistratorInfo.objects.update_or_create(
        submission=submission, defaults=registrator_auth
    )
