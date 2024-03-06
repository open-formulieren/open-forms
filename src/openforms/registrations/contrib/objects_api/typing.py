from typing import Literal, TypeAlias, TypedDict

from typing_extensions import Required

ConfigVersion: TypeAlias = Literal[1, 2]


class _BaseRegistrationOptions(TypedDict, total=False):
    objecttype: Required[str]
    objecttype_version: Required[int]
    productaanvraag_type: str
    informatieobjecttype_submission_report: str
    upload_submission_csv: bool
    informatieobjecttype_submission_csv: str
    informatieobjecttype_attachment: str
    organisatie_rsin: str


class RegistrationOptionsV1(_BaseRegistrationOptions, total=False):
    version: Required[Literal[1]]
    content_json: str
    payment_status_update_json: str


class ObjecttypeVariableMapping(TypedDict):
    variable_key: str
    target_path: list[str]


class RegistrationOptionsV2(_BaseRegistrationOptions):
    version: Literal[2]
    variables_mapping: list[ObjecttypeVariableMapping]


RegistrationOptions: TypeAlias = RegistrationOptionsV1 | RegistrationOptionsV2
"""The Objects API registration options (either V1 or V2)."""
