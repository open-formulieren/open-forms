import logging
from io import BytesIO

from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport
from openforms.translations.utils import to_iso639_2b

from .clients.documenten import DocumentenClient

logger = logging.getLogger(__name__)


def create_report_document(
    client: DocumentenClient,
    name: str,
    submission_report: SubmissionReport,
    options: dict,
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
            language=to_iso639_2b(submission_report.submission.language_code),
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
    options: dict,
    language: str = "nld",
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
    options: dict,
) -> dict:
    """
    Create a document for a submission attachment (user upload).
    """
    submission = submission_attachment.submission_step.submission
    with submission_attachment.content.open("rb") as content:
        return client.create_document(
            informatieobjecttype=options["informatieobjecttype"],
            bronorganisatie=options["organisatie_rsin"],
            title=options.get("titel") or name,
            author=options.get("auteur") or "Aanvrager",
            language=to_iso639_2b(
                submission.language_code
            ),  # assume same as submission
            format=submission_attachment.content_type,
            content=content,
            status="definitief",
            filename=submission_attachment.get_display_name(),
            description="Bijgevoegd document",
            vertrouwelijkheidaanduiding=options.get(
                "doc_vertrouwelijkheidaanduiding", ""
            ),
        )
