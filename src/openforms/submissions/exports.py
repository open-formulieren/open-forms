from django.http import FileResponse
from django.utils.timezone import make_naive

import tablib


def export_submissions(queryset, file_type):
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
            submission.form.public_name,
            inzending_datum,
        ]
        merged_data = submission.get_merged_data()
        for header in headers:
            submission_data.append(merged_data.get(header))
        data.append(submission_data)
    filename = f"submissions_export.{file_type}"
    response = FileResponse(
        data.export(file_type), filename=filename, as_attachment=True
    )
    response.set_headers(response.streaming_content)

    return response
