from typing import NotRequired, TypedDict


class DocumentOptions(TypedDict):
    informatieobjecttype: str
    organisatie_rsin: str
    auteur: NotRequired[str]
    doc_vertrouwelijkheidaanduiding: NotRequired[str]
    ontvangstdatum: NotRequired[str]
    titel: NotRequired[str]
