from openforms.authentication.types import AnyAuthContext

from .constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from .typing import BaseAuth
from .utils import (
    check_user_is_submission_initiator,
    is_authenticated_with_an_allowed_plugin,
    is_authenticated_with_plugin,
    remove_auth_info_from_session,
    store_auth_details,
)

__all__ = [
    "FORM_AUTH_SESSION_KEY",
    "AuthAttribute",
    "BaseAuth",
    "check_user_is_submission_initiator",
    "store_auth_details",
    "is_authenticated_with_plugin",
    "is_authenticated_with_an_allowed_plugin",
    "remove_auth_info_from_session",
]


def get_branch_number(auth_context: AnyAuthContext) -> str:
    if auth_context["source"] != "eherkenning":
        return ""
    legal_subject = auth_context["authorizee"]["legalSubject"]
    return legal_subject.get("branchNumber", "")
