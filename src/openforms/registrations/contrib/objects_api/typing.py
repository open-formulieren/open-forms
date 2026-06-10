from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, NotRequired, Required, TypedDict
from uuid import UUID

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.zgw.typing import VertrouwelijkheidAanduiding

type ConfigVersion = Literal[1, 2]

type TargetPath = list[str]


class CatalogueOption(TypedDict):
    domain: str
    rsin: str


class FileComponentOptions(TypedDict, total=False):
    document_type_description: str
    organization_rsin: str
    confidentiality_level: VertrouwelijkheidAanduiding
    title: str


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
    auth_attribute_path: Required[TargetPath]

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

    files: NotRequired[Mapping[str, FileComponentOptions]]
    """
    Mapping from component key to file upload options for the Documents API.

    The key is the component key and can contain ``.`` characters. No nesting is
    created, it's the literal key string as defined on the component.

    Keys may refer to file components inside editgrid components too. We rely on the
    admin enforcing key uniqueness for *all* components in the form, which is stricter
    than vanilla Formio.
    """


class RegistrationOptionsV1(_BaseRegistrationOptions, total=False):
    version: Required[Literal[1]]
    productaanvraag_type: str
    content_json: str
    payment_status_update_json: str


class AddressNLObjecttypeVariableMapping(TypedDict, total=False):
    postcode: TargetPath
    house_letter: TargetPath
    house_number: TargetPath
    house_number_addition: TargetPath
    city: TargetPath
    street_name: TargetPath


class ObjecttypeVariableMapping(TypedDict):
    variable_key: str
    target_path: NotRequired[TargetPath]
    options: NotRequired[AddressNLObjecttypeVariableMapping]


class RegistrationOptionsV2(_BaseRegistrationOptions, total=False):
    version: Required[Literal[2]]
    variables_mapping: Required[list[ObjecttypeVariableMapping]]
    geometry_variable_key: str
    transform_to_list: Required[list[str]]


type RegistrationOptions = RegistrationOptionsV1 | RegistrationOptionsV2
"""The Objects API registration options (either V1 or V2)."""
