from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
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
    zaaktype: str  # DeprecationWarning
    informatieobjecttype: str
    organisatie_rsin: NotRequired[str]
    zaak_vertrouwelijkheidaanduiding: NotRequired[VertrouwelijkheidAanduiding]
    medewerker_roltype: NotRequired[str]
    objecttype: NotRequired[str]
    objecttype_version: NotRequired[int]
    content_json: NotRequired[str]
    property_mappings: NotRequired[list[PropertyMapping]]
    # keys set in ZGWApiGroupConfig.apply_defaults_to
    doc_vertrouwelijkheidaanduiding: NotRequired[VertrouwelijkheidAanduiding]
    auteur: NotRequired[str]
