import os.path
import pathlib
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.urls import Resolver404, resolve
from django.utils.translation import gettext as _

import PIL
import structlog
from glom import Path, glom
from PIL import Image

from openforms.api.exceptions import RequestEntityTooLarge
from openforms.conf.utils import Filesize
from openforms.formio.service import FormioData, iterate_data_with_components
from openforms.formio.typing import Component
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionStep,
    TemporaryFileUpload,
)
from openforms.template import render_from_string, sandbox_backend
from openforms.typing import JSONObject
from openforms.utils.glom import _glom_path_to_str

logger = structlog.stdlib.get_logger(__name__)

DEFAULT_IMAGE_MAX_SIZE = (10000, 10000)

# validate the size as Formio does (client-side) - meaning 1MB is actually 1MiB
# https://github.com/formio/formio.js/blob/4.12.x/src/components/file/File.js#L523
file_size_cast = Filesize(system=Filesize.S_BINARY)


def temporary_upload_uuid_from_url(url: str) -> str | None:
    try:
        match = resolve(urlparse(url)[2])
    except Resolver404:
        return None
    else:
        if match.view_name == "api:submissions:temporary-file":
            return str(match.kwargs["uuid"])
        else:
            return None


def temporary_upload_from_url(url: str) -> TemporaryFileUpload | None:
    uuid = temporary_upload_uuid_from_url(url)
    if not uuid:
        return None
    try:
        return TemporaryFileUpload.objects.get(uuid=uuid)
    except TemporaryFileUpload.DoesNotExist:
        return None


def clean_mime_type(mimetype: str) -> str:
    # cleanup a user supplied mime-type against injection attacks
    m = re.match(r"^[a-z0-9\.+-]+\/[a-z0-9\.+-]+", mimetype)
    if not m:
        return "application/octet-stream"
    else:
        return m.group()


def append_file_num_postfix(
    original_name: str, new_name: str, num: int, max: int
) -> str:
    if not new_name:
        return ""

    _, ext = os.path.splitext(original_name)
    new_name, _ = os.path.splitext(new_name)
    if max <= 1:
        postfix = ""
    else:
        digits = len(str(max))
        postfix = f"-{num:0{digits}}"
    return f"{new_name}{postfix}{ext}"


@dataclass
class UploadContext:
    upload: TemporaryFileUpload
    component: Component
    index: int  # one-based
    form_key: str  # formio key
    data_path: str  # The path to the component data in the submission data
    configuration_path: str  # The path to the component in the configuration JSON
    num_uploads: int


def iter_step_uploads(
    submission_step: SubmissionStep, data: FormioData | None = None
) -> Iterator[UploadContext]:
    """
    Iterate over all the uploads for a given submission step.

    Yield every uploaded file and its context within the form step for further
    processing.
    """
    data = data or submission_step.data
    uploads = resolve_uploads_from_data(
        submission_step.form_step.form_definition.configuration, data
    )
    for data_path, (component, upload_instances, configuration_path) in uploads.items():
        # formio sends a list of uploads even with multiple=False
        for i, upload in enumerate(upload_instances, start=1):
            yield UploadContext(
                upload=upload,
                form_key=component["key"],
                component=component,
                index=i,
                num_uploads=len(upload_instances),
                data_path=data_path,
                configuration_path=configuration_path,
            )


def attach_uploads_to_submission_step(
    submission_step: SubmissionStep,
) -> list[tuple[SubmissionFileAttachment, bool]]:
    # circular import
    from .tasks import resize_submission_attachment

    result = list()

    variable_state = submission_step.submission.load_submission_value_variables_state()
    step_variables = variable_state.get_variables_in_submission_step(submission_step)

    for upload_context in iter_step_uploads(submission_step):
        upload, component, key, data_path, configuration_path = (
            upload_context.upload,
            upload_context.component,
            upload_context.form_key,
            Path.from_text(upload_context.data_path),
            upload_context.configuration_path,
        )

        submission_variable = step_variables.get(key)
        if not submission_variable:
            # This is the case for fields inside repeating groups. We need to find the variable of the parent group
            # to which they belong
            for index in range(len(data_path) - 1, 0, -1):
                submission_variable = glom(
                    step_variables, data_path[:index], default=None
                )
                if submission_variable:
                    break

        # TODO decide what it means if this fails
        assert submission_variable is not None

        # grab resize settings
        resize_apply = glom(component, "of.image.resize.apply", default=False)
        resize_size = (
            glom(component, "of.image.resize.width", default=DEFAULT_IMAGE_MAX_SIZE[0]),
            glom(
                component, "of.image.resize.height", default=DEFAULT_IMAGE_MAX_SIZE[1]
            ),
        )
        file_max_size = file_size_cast(
            glom(component, "fileMaxSize", default="") or settings.MAX_FILE_UPLOAD_SIZE
        )

        base_name = render_from_string(
            source=glom(component, "file.name", default=""),
            context={"fileName": pathlib.Path(upload.file_name).stem},
            backend=sandbox_backend,
        )

        if upload.file_size > file_max_size:
            raise RequestEntityTooLarge(
                _(
                    "Upload {uuid} exceeds the maximum upload size of {max_size}b"
                ).format(
                    uuid=upload.uuid,
                    max_size=file_max_size,
                ),
            )

        file_name = append_file_num_postfix(
            upload.file_name,
            base_name,
            upload_context.index,
            upload_context.num_uploads,
        )

        (
            attachment,
            created,
        ) = SubmissionFileAttachment.objects.get_or_create_from_upload(
            submission_step,
            submission_variable,
            configuration_path,
            _glom_path_to_str(data_path),
            upload,
            file_name=file_name,
        )
        result.append((attachment, created))

        if created and resize_apply and resize_size:
            # NOTE there is a possible race-condition if user completes a submission before this resize task is done
            # see https://github.com/open-formulieren/open-forms/issues/507
            transaction.on_commit(
                partial(resize_submission_attachment.delay, attachment.id, resize_size)
            )

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


def resolve_uploads_from_data(configuration: JSONObject, data: FormioData) -> dict:
    """
    "my_file": [
        {
            "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
            "data": {
                "url": "http://server/api/v2/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
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

    for component_with_data_item in iterate_data_with_components(
        configuration, data, filter_types=["file"]
    ):
        uploads = list()
        for info in component_with_data_item.upload_info:
            # let's be careful with malformed user data
            if not isinstance(info, dict) or not isinstance(info.get("url"), str):
                continue

            upload = temporary_upload_from_url(info["url"])
            if upload:
                uploads.append(upload)

        if uploads:
            result[component_with_data_item.data_path] = (
                component_with_data_item.component,
                uploads,
                component_with_data_item.configuration_path,
            )

    return result


def resize_attachment(
    attachment: SubmissionFileAttachment, size: tuple[int, int]
) -> bool:
    """
    'safe' resize an attached image that might not be an image or not need resize at all
    """
    try:
        # this might not actually be an image file; let's open it and see
        image = Image.open(
            attachment.content,
            formats=(
                "png",
                "jpeg",
            ),
        )
    except PIL.UnidentifiedImageError:
        # oops
        return False
    except OSError:
        # more specific
        return False
    except ValueError:
        # more specific
        return False
    else:
        # check if we have work
        if image.width <= size[0] and image.height <= size[1]:
            return False

        # TODO SpooledTemporaryFile but what limit?
        with NamedTemporaryFile() as tmp:
            image.thumbnail(size)
            image.save(tmp, image.format)
            attachment.content.save(attachment.content.name, tmp, save=True)
            return True
