from typing import Literal, Optional, TypedDict

from openforms.submissions.models import Submission

from .constants import FORM_AUTH_SESSION_KEY, AuthAttribute
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


def store_auth_details(
    submission: Submission, form_auth: FormAuth, attribute_hashed: bool = False
) -> None:
    attribute = form_auth["attribute"]
    if attribute not in AuthAttribute.values:
        raise ValueError(f"Unexpected auth attribute {attribute} specified")

    AuthInfo.objects.update_or_create(
        submission=submission,
        defaults={**form_auth, **{"attribute_hashed": attribute_hashed}},
    )


def store_registrator_details(
    submission: Submission, registrator_auth: BaseAuth
) -> None:
    attribute = registrator_auth["attribute"]
    if attribute not in AuthAttribute.values:
        raise ValueError(f"Unexpected auth attribute {attribute} specified")

    RegistratorInfo.objects.update_or_create(
        submission=submission, defaults=registrator_auth
    )


def has_valid_authentication_for_cosign(request, expected_plugin) -> bool:
    if FORM_AUTH_SESSION_KEY not in request.session:
        return False

    auth_data = request.session[FORM_AUTH_SESSION_KEY]
    if auth_data["plugin"] == expected_plugin:
        return True

    return False
