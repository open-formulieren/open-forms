from io import BytesIO
from typing import Literal, NotRequired, TypedDict

from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport

from .clients.documenten import DocumentenClient

type SupportedLanguage = Literal["nl", "en"]


class DocumentOptions(TypedDict):
    informatieobjecttype: str
    organisatie_rsin: str
    auteur: NotRequired[str]
    doc_vertrouwelijkheidaanduiding: NotRequired[str]
    ontvangstdatum: NotRequired[str]
    titel: NotRequired[str]


def create_report_document(
    client: DocumentenClient,
    name: str,
    submission_report: SubmissionReport,
    options: DocumentOptions,
    language: SupportedLanguage,
) -> dict:
    """
    Create a document for the summary PDF.
    """
    with submission_report.content.open("rb") as content:
        return client.create_document(
            informatieobjecttype=options["informatieobjecttype"],
            bronorganisatie=options["organisatie_rsin"],
            title=name,
            author=options.get("auteur") or "Aanvrager",
            language=language,
            format="application/pdf",
            content=content,
            status="definitief",
            filename=f"open-forms-{name}.pdf",
            description="Ingezonden formulier",
            vertrouwelijkheidaanduiding=options.get(
                "doc_vertrouwelijkheidaanduiding", ""
            ),
        )


def create_csv_document(
    client: DocumentenClient,
    name: str,
    csv_data: str,
    options: DocumentOptions,
    language: SupportedLanguage,
) -> dict:
    content = BytesIO(csv_data.encode())
    return client.create_document(
        informatieobjecttype=options["informatieobjecttype"],
        bronorganisatie=options["organisatie_rsin"],
        title=name,
        author=options.get("auteur") or "Aanvrager",
        language=language,
        format="text/csv",
        content=content,
        status="definitief",
        filename=f"open-forms-{name}.csv",
        description="Ingezonden formulierdata",
        vertrouwelijkheidaanduiding=options.get("doc_vertrouwelijkheidaanduiding", ""),
    )


def create_attachment_document(
    client: DocumentenClient,
    name: str,
    submission_attachment: SubmissionFileAttachment,
    options: DocumentOptions,
    language: SupportedLanguage,
) -> dict:
    """
    Create a document for a submission attachment (user upload).
    """
    with submission_attachment.content.open("rb") as content:
        return client.create_document(
            informatieobjecttype=options["informatieobjecttype"],
            bronorganisatie=options["organisatie_rsin"],
            title=options.get("titel") or name,
            author=options.get("auteur") or "Aanvrager",
            language=language,
            format=submission_attachment.content_type,
            content=content,
            status="definitief",
            filename=submission_attachment.get_display_name(),
            description="Bijgevoegd document",
            received_date=options.get("ontvangstdatum"),
            vertrouwelijkheidaanduiding=options.get(
                "doc_vertrouwelijkheidaanduiding", ""
            ),
        )
