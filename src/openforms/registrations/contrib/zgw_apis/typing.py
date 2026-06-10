from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING, Literal, NotRequired, Required, TypedDict

from openforms.contrib.zgw.typing import VertrouwelijkheidAanduiding

from .constants import SummaryDocumentChoices

if TYPE_CHECKING:
    from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

    from .models import ZGWApiGroupConfig


class CatalogueOption(TypedDict):
    domain: str
    rsin: str


class PropertyMapping(TypedDict):
    component_key: str
    eigenschap: str


class FileComponentOptions(TypedDict, total=False):
    key: Required[str]
    document_type_description: str
    organization_rsin: str
    confidentiality_level: VertrouwelijkheidAanduiding
    title: str


class RegistrationOptions(TypedDict):
    zgw_api_group: ZGWApiGroupConfig
    catalogue: CatalogueOption
    case_type_identification: str
    document_type_description: str
    product_url: str  # URL reference to a product in the case type
    zaaktype: str  # DeprecationWarning
    informatieobjecttype: str  # DeprecationWarning
    organisatie_rsin: NotRequired[str]
    zaak_vertrouwelijkheidaanduiding: NotRequired[
        VertrouwelijkheidAanduiding | Literal[""]
    ]
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
    zaak_omschrijving: NotRequired[str]
    zaak_toelichting: NotRequired[str]
    summary_documents: Collection[SummaryDocumentChoices]
    files: NotRequired[Collection[FileComponentOptions]]
    """
    List of file upload options for the Documents API.

    Each item contains at least the Formio component ``key`` key, which can contain
    ``.`` characters. It's the literal key string as defined on the component.

    Keys may refer to file components inside editgrid components too. We rely on the
    admin enforcing key uniqueness for *all* components in the form, which is stricter
    than vanilla Formio.
    """
