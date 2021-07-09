from datetime import timedelta
from typing import Iterable, Optional
from urllib.parse import urlparse

from django.urls import Resolver404, resolve

from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionStep,
    TemporaryFileUpload,
)


def temporary_upload_uuid_from_url(url: str) -> Optional[str]:
    try:
        match = resolve(urlparse(url)[2])
    except Resolver404:
        return None
    else:
        if match.view_name == "api:submissions:temporary-file":
            return str(match.kwargs["uuid"])
        else:
            return None


def temporary_upload_from_url(url: str) -> Optional[TemporaryFileUpload]:
    uuid = temporary_upload_uuid_from_url(url)
    if not uuid:
        return None
    try:
        return TemporaryFileUpload.objects.get(uuid=uuid)
    except TemporaryFileUpload.DoesNotExist:
        return None


def attach_uploads_to_submission_step(submission_step: SubmissionStep) -> dict:
    # TODO replace this add-hoc iterator with form_step.iter_components(recursive=True) once it merges

    # components = list(submission_step.form_step.iter_components(recursive=True))

    def _iter_components(components):
        for c in components:
            yield c
            if c.get("components"):
                yield from _iter_components(c["components"])

    components = submission_step.form_step.form_definition.configuration["components"]
    components = list(_iter_components(components))

    #  TODO end

    uploads = resolve_uploads_from_data(components, submission_step.data)

    result = list()
    for key, (component, uploads) in uploads.items():
        for upload in uploads:
            # TODO reformat the name (or grab from formio)
            # TODO validate data from component settings
            # TODO do we need to de-duplicate?
            attachment, created = SubmissionFileAttachment.objects.create_from_upload(
                submission_step, key, upload
            )
            result.append((attachment, created))

    return result


def cleanup_submission_temporary_uploaded_files(submission: Submission):
    for attachment in SubmissionFileAttachment.objects.for_submission(
        submission
    ).filter(temporary_file__isnull=False):
        attachment.temporary_file.delete()


def cleanup_unclaimed_temporary_uploaded_files(age=timedelta(days=2)):
    for file in TemporaryFileUpload.objects.select_prune(age).filter(attachments=None):
        file.delete()


def iter_component_data(components: Iterable[dict], data: dict, filter_types=None):
    if not data or not components:
        return
    for component in components:
        key = component.get("key")
        type = component.get("type")
        if not key or not type:
            continue
        if key not in data:
            continue
        if filter_types and type not in filter_types:
            continue
        yield component, data[key]


def resolve_uploads_from_data(components: Iterable[dict], data: dict) -> dict:
    """
    "my_file": [
        {
            "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
            "data": {
                "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                "form": "",
                "name": "my-image.jpg",
                "size": 46114,
                "baseUrl": "http://server/form",
                "project": "",
            },
            "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
            "size": 46114,
            "type": "image/jpg",
            "storage": "url",
            "originalName": "my-image.jpg",
        }
    ]
    """
    result = dict()

    for component, upload_info in iter_component_data(
        components, data, filter_types={"file"}
    ):
        key = component["key"]
        uploads = list()
        for info in upload_info:
            # lets be careful with malformed user data
            if not isinstance(info, dict) or not isinstance(info.get("url"), str):
                continue

            upload = temporary_upload_from_url(info["url"])
            if not upload:
                continue
            # TODO we might also need to pickup formio's formatted name
            uploads.append(upload)

        if uploads:
            result[key] = (component, uploads)

    return result
