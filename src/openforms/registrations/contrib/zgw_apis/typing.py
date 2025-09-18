from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
    from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

    from .models import ZGWApiGroupConfig


class CatalogueOption(TypedDict):
    domain: str
    rsin: str


class PropertyMapping(TypedDict):
    component_key: str
    eigenschap: str


type VertrouwelijkheidAanduiding = Literal[
    "openbaar",
    "beperkt_openbaar",
    "intern",
    "zaakvertrouwelijk",
    "vertrouwelijk",
    "confidentieel",
    "geheim",
    "zeer_geheim",
]


class RegistrationOptions(TypedDict):
    zgw_api_group: ZGWApiGroupConfig
    catalogue: NotRequired[CatalogueOption]
    case_type_identification: str
    document_type_description: str
    product_url: str  # URL reference to a product in the case type
    zaaktype: str  # DeprecationWarning
    informatieobjecttype: str  # DeprecationWarning
    organisatie_rsin: NotRequired[str]
    zaak_vertrouwelijkheidaanduiding: NotRequired[VertrouwelijkheidAanduiding]
    medewerker_roltype: NotRequired[str]
    partners_roltype: str
    partners_description: str
    children_roltype: str
    children_description: str
    objects_api_group: ObjectsAPIGroupConfig | None
    objecttype: NotRequired[str]
    objecttype_version: NotRequired[int]
    content_json: NotRequired[str]
    property_mappings: NotRequired[list[PropertyMapping]]
    # keys set in ZGWApiGroupConfig.apply_defaults_to
    doc_vertrouwelijkheidaanduiding: NotRequired[VertrouwelijkheidAanduiding]
    auteur: NotRequired[str]
