from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NotRequired, Required, TypedDict
from uuid import UUID

if TYPE_CHECKING:
    from .models import ObjectsAPIGroupConfig


type ConfigVersion = Literal[1, 2]


class CatalogueOption(TypedDict):
    domain: str
    rsin: str


class _BaseRegistrationOptions(TypedDict, total=False):
    # which services to use
    objects_api_group: Required[ObjectsAPIGroupConfig]

    # which catalogue in the Catalogi API to use (for lookups/validation)
    catalogue: CatalogueOption

    # which object type to use for the registration & how does it interact with
    # initial data reference
    objecttype: Required[UUID]
    objecttype_version: Required[int]
    update_existing_object: Required[bool]
    auth_attribute_path: Required[list[str]]

    # metadata of documents created in the documents API
    upload_submission_csv: bool
    organisatie_rsin: str

    # Required -> serializer provides `default=""`
    iot_submission_report: Required[str]
    iot_submission_csv: Required[str]
    iot_attachment: Required[str]

    # DeprecationWarning: URL properties will be removed in OF 4.0
    informatieobjecttype_submission_report: str
    informatieobjecttype_submission_csv: str
    informatieobjecttype_attachment: str


class RegistrationOptionsV1(_BaseRegistrationOptions, total=False):
    version: Required[Literal[1]]
    productaanvraag_type: str
    content_json: str
    payment_status_update_json: str


class AddressNLObjecttypeVariableMapping(TypedDict):
    postcode: NotRequired[list[str]]
    house_letter: NotRequired[list[str]]
    house_number: NotRequired[list[str]]
    house_number_addition: NotRequired[list[str]]
    city: NotRequired[list[str]]
    street_name: NotRequired[list[str]]


class ObjecttypeVariableMapping(TypedDict):
    variable_key: str
    target_path: NotRequired[list[str]]
    options: NotRequired[AddressNLObjecttypeVariableMapping]


class RegistrationOptionsV2(_BaseRegistrationOptions, total=False):
    version: Required[Literal[2]]
    variables_mapping: Required[list[ObjecttypeVariableMapping]]
    geometry_variable_key: str


type RegistrationOptions = RegistrationOptionsV1 | RegistrationOptionsV2
"""The Objects API registration options (either V1 or V2)."""
