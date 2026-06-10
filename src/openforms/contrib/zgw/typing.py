from typing import Literal, NotRequired, TypedDict

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


class DocumentOptions(TypedDict):
    informatieobjecttype: str
    organisatie_rsin: str
    auteur: NotRequired[str]
    doc_vertrouwelijkheidaanduiding: NotRequired[str]
    ontvangstdatum: NotRequired[str]
    titel: NotRequired[str]
