import dataclasses

from django.http import FileResponse, HttpResponse
from django.utils.timezone import make_naive

import tablib

from .query import SubmissionQuerySet


@dataclasses.dataclass
class FileType:
    extension: str
    content_type: str


class ExportFileTypes:
    CSV = FileType("csv", "text/csv")
    XLSX = FileType(
        "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def create_submission_export(queryset: SubmissionQuerySet) -> tablib.Dataset:
    headers = []
    for submission in queryset:
        headers += list(submission.get_merged_data().keys())
    headers = list(dict.fromkeys(headers))  # Remove duplicates
    data = tablib.Dataset(headers=["Formuliernaam", "Inzendingdatum"] + headers)
    for submission in queryset:
        inzending_datum = (
            make_naive(submission.completed_on) if submission.completed_on else None
        )
        submission_data = [
            submission.form.admin_name,
            inzending_datum,
        ]
        merged_data = submission.get_merged_data()
        for header in headers:
            submission_data.append(merged_data.get(header))
        data.append(submission_data)
    return data


def export_submissions(
    queryset: SubmissionQuerySet, file_type: FileType
) -> FileResponse:
    export_data = create_submission_export(queryset)
    filename = f"submissions_export.{file_type.extension}"

    response = HttpResponse(
        export_data.export(file_type.extension),
        content_type=file_type.content_type,
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
