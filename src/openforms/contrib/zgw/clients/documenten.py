from base64 import b64encode
from typing import BinaryIO, Literal, TypeAlias

from django.core.files.base import ContentFile

from zgw_consumers_ext.api_client import NLXClient

from .utils import get_today

DocumentStatus: TypeAlias = Literal[
    "in_bewerking",
    "ter_vaststelling",
    "definitief",
    "gearchiveerd",
]

ENDPOINT_MAP = {
    "enkelvoudiginformatieobject": "enkelvoudiginformatieobjecten",
}


class DocumentenClient(NLXClient):
    def create_document(
        self,
        informatieobjecttype: str,
        bronorganisatie: str,
        title: str,
        author: str,
        language: str,
        format: str,
        content: ContentFile | BinaryIO,
        status: DocumentStatus,
        filename: str,
        description: str = "",
        vertrouwelijkheidaanduiding: str = "",
    ):
        assert author, "athor must be a non-empty string"
        today = get_today()
        base64_body = b64encode(content.read()).decode()
        data = {
            "informatieobjecttype": informatieobjecttype,
            "bronorganisatie": bronorganisatie,
            "creatiedatum": today,
            "titel": title,
            "auteur": author,
            "taal": language,
            "formaat": format,
            "inhoud": base64_body,
            "status": status,
            "bestandsnaam": filename,
            "beschrijving": description,
            "indicatieGebruiksrecht": False,
        }

        if vertrouwelijkheidaanduiding:
            data["vertrouwelijkheidaanduiding"] = vertrouwelijkheidaanduiding

        response = self.post("enkelvoudiginformatieobjecten", json=data)
        response.raise_for_status()

        return response.json()

    # TEMPORARY implementation while we refactor the API clients & satisfying the type
    # checkers.

    def list(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def create(self, resource: str, data: dict, **kwargs) -> dict:
        endpoint = ENDPOINT_MAP[resource]
        response = self.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def partial_update(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError
