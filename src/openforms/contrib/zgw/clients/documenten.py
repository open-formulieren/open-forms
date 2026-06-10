from base64 import b64encode
from io import BytesIO
from typing import Literal, assert_never

from django.core.files import File

from zgw_consumers.nlx import NLXClient

from openforms.contrib.client import LoggingMixin
from openforms.translations.utils import to_iso639_2b
from openforms.utils.date import get_today

type DocumentStatus = Literal[
    "in_bewerking",
    "ter_vaststelling",
    "definitief",
    "gearchiveerd",
]


class DocumentenClient(LoggingMixin, NLXClient):
    def create_document(
        self,
        informatieobjecttype: str,
        bronorganisatie: str,
        title: str,
        author: str,
        language: str,
        format: str,
        content: File | BytesIO,
        status: DocumentStatus,
        filename: str,
        received_date: str | None = None,
        description: str = "",
        vertrouwelijkheidaanduiding: str = "",
    ):
        assert author, "author must be a non-empty string"
        today = get_today().isoformat()
        file_content = content.read()

        file_size: int
        match content:
            case File():
                file_size = content.size
            case BytesIO():
                file_size = len(file_content)
            case _:  # pragma: no cover
                assert_never(content)

        base64_body = b64encode(file_content).decode()
        data = {
            "informatieobjecttype": informatieobjecttype,
            "bronorganisatie": bronorganisatie,
            "creatiedatum": today,
            "titel": title,
            "auteur": author,
            "taal": to_iso639_2b(language),
            "formaat": format,
            "inhoud": base64_body,
            "status": status,
            "bestandsnaam": filename,
            "ontvangstdatum": received_date,
            "beschrijving": description,
            "indicatieGebruiksrecht": False,
            "bestandsomvang": file_size,
        }

        if vertrouwelijkheidaanduiding:
            data["vertrouwelijkheidaanduiding"] = vertrouwelijkheidaanduiding

        response = self.post("enkelvoudiginformatieobjecten", json=data)
        response.raise_for_status()

        return response.json()
