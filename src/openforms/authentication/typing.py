from typing import NotRequired, TypedDict

from openforms.typing import JSONObject

from .constants import AuthAttribute


class BaseAuth(TypedDict):
    """The base structure of authentication data."""

    plugin: str
    """The unique identifier of the plugin that inititiated the authentication data."""

    attribute: AuthAttribute
    value: str


class FormAuth(BaseAuth):
    loa: NotRequired[str]
    additional_claims: NotRequired[dict]
    acting_subject_identifier_type: NotRequired[str]
    acting_subject_identifier_value: NotRequired[str]
    legal_subject_identifier_type: NotRequired[str]
    legal_subject_identifier_value: NotRequired[str]
    legal_subject_service_restriction: NotRequired[str]
    mandate_context: NotRequired[JSONObject]
