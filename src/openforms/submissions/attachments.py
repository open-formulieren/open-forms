import logging
import os.path
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.urls import Resolver404, resolve
from django.utils.translation import gettext as _

import magic
import PIL
from glom import Path, glom
from PIL import Image
from rest_framework.exceptions import ErrorDetail, ValidationError

from openforms.api.exceptions import RequestEntityTooLarge
from openforms.conf.utils import Filesize
from openforms.config.models import GlobalConfiguration
from openforms.formio.service import mimetype_allowed
from openforms.formio.typing import Component
from openforms.formio.utils import get_all_component_keys, iter_components
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionStep,
    TemporaryFileUpload,
)
from openforms.typing import JSONObject
from openforms.utils.glom import _glom_path_to_str

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_MAX_SIZE = (10000, 10000)

# validate the size as Formio does (client-side) - meaning 1MB is actually 1MiB
# https://github.com/formio/formio.js/blob/4.12.x/src/components/file/File.js#L523
file_size_cast = Filesize(system=Filesize.S_BINARY)


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


def _iterate_data_with_components(
    configuration: JSONObject,
    data: JSONObject,
    data_path: Path = Path(),
    configuration_path: str = "components",
    filter_types: List[str] = None,
) -> Optional[Tuple[JSONObject, JSONObject, str, str]]:
    """
    Iterate through a configuration and return a tuple with the component JSON, its value in the submission data
    and the path within the submission data.

    For example, for a configuration with components:

    .. code:: json

        [
            {"key": "surname", "type": "textfield"},
            {"key": "pets", "type": "editgrid", "components": [{"key": "name", "type": "textfield"}]}
        ]

    And a submission data:

    .. code:: json

        {"surname": "Doe", "pets": [{"name": "Qui"}, {"name": "Quo"}, {"name": "Qua"}] }

    For the "Qui" item of the repeating group this function would yield:
    ``({"key": "name", "type": "textfield"}, "Qui", "pets.0.name")``.
    """
    if configuration.get("type") == "columns":
        for index, column in enumerate(configuration["columns"]):
            child_configuration_path = f"{configuration_path}.columns.{index}"
            yield from _iterate_data_with_components(
                column, data, data_path, child_configuration_path, filter_types
            )

    parent_type = configuration.get("type")
    if parent_type == "editgrid":
        parent_path = Path(data_path, Path.from_text(configuration["key"]))
        group_data = glom(data, parent_path, default=list())
        for index in range(len(group_data)):
            yield from _iterate_data_with_components(
                {"components": configuration.get("components", [])},
                data,
                data_path=Path(parent_path, index),
                configuration_path=f"{configuration_path}.components",
                filter_types=filter_types,
            )
    else:
        base_configuration_path = configuration_path
        if parent_type == "fieldset":
            base_configuration_path += ".components"
        for index, child_component in enumerate(configuration.get("components", [])):
            child_configuration_path = f"{base_configuration_path}.{index}"
            yield from _iterate_data_with_components(
                child_component, data, data_path, child_configuration_path, filter_types
            )

    filter_out = (parent_type not in filter_types) if filter_types else False
    if "key" in configuration and not filter_out:
        component_data_path = Path(data_path, Path.from_text(configuration["key"]))
        component_data = glom(data, component_data_path, default=None)
        if component_data is not None:
            yield configuration, component_data, _glom_path_to_str(
                component_data_path
            ), configuration_path


def iter_step_uploads(
    submission_step: SubmissionStep, data=None
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


def validate_uploads(submission_step: SubmissionStep, data: Optional[dict]) -> None:
    """
    Validate the file uploads in the submission step data.

    File uploads are stored in a temporary file uploads table and the references to them
    are included in the step submission data. This function validates that the actual
    content and metadata of files conforms to the configured file upload components.
    """
    validation_errors = defaultdict(list)
    config = GlobalConfiguration.get_solo()
    for upload_context in iter_step_uploads(submission_step, data=data):
        upload, component, key = (
            upload_context.upload,
            upload_context.component,
            upload_context.form_key,
        )

        if component.get("useConfigFiletypes"):
            allowed_mime_types = config.form_upload_default_file_types
        else:
            allowed_mime_types = glom(component, "file.type", default=[])

        # perform content type validation
        with upload.content.open("rb") as infile:
            # 2048 bytes per recommendation of python-magic
            head = infile.read(2048)
            file_mime_type = magic.from_buffer(head, mime=True)

            # gh #2520
            if file_mime_type == "application/CDFV2":
                whole_file = head + infile.read()
                file_mime_type = magic.from_buffer(whole_file, mime=True)

        invalid_file_type_error = ErrorDetail(
            _("The file '{filename}' is not a valid file type.").format(
                filename=upload.file_name
            ),
            code="invalid",
        )

        if upload.content_type != file_mime_type:
            validation_errors[key].append(invalid_file_type_error)
            continue

        # validate that the mime type passes the allowlist
        if not mimetype_allowed(file_mime_type, allowed_mime_types):
            logger.warning(
                "Blocking submission upload %d because of invalid mime type check",
                upload.id,
            )
            validation_errors[key].append(invalid_file_type_error)
            continue

    if validation_errors:
        raise ValidationError(validation_errors)


def _get_repeating_group_keys(configuration):
    keys = []
    for component in iter_components(configuration, recursive=False):
        if component["type"] == "editgrid":
            for nested in iter_components(component, recursive=False):
                keys.append(nested["key"])
                keys += _get_repeating_group_keys(nested)
    return keys


def attach_uploads_to_submission_step(submission_step: SubmissionStep) -> list:
    # circular import
    from .tasks import resize_submission_attachment

    result = list()

    config = submission_step.form_step.form_definition.configuration
    all_component_keys = get_all_component_keys(config)
    repeating_group_keys = _get_repeating_group_keys(config)

    for upload_context in iter_step_uploads(submission_step):
        upload, component, key, data_path, configuration_path = (
            upload_context.upload,
            upload_context.component,
            upload_context.form_key,
            Path.from_text(upload_context.data_path),
            upload_context.configuration_path,
        )

        # GH#2699 - properly map to repeating group key
        if key in repeating_group_keys:
            for index in range(len(data_path) - 1, 0, -1):
                _key = _glom_path_to_str(data_path[:index])
                if _key not in repeating_group_keys and _key in all_component_keys:
                    key = _key
                    break

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

        base_name = glom(component, "file.name", default="")

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
            form_key=key,
            configuration_path=configuration_path,
            data_path=_glom_path_to_str(data_path),
            upload=upload,
            file_name=file_name,
        )
        result.append((attachment, created))

        if created and resize_apply and resize_size:
            # NOTE there is a possible race-condition if user completes a submission before this resize task is done
            # see https://github.com/open-formulieren/open-forms/issues/507
            transaction.on_commit(
                lambda: resize_submission_attachment.delay(attachment.id, resize_size)
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


def resolve_uploads_from_data(configuration: JSONObject, data: dict) -> dict:
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

    for (
        component,
        upload_info,
        data_path,
        configuration_path,
    ) in _iterate_data_with_components(configuration, data, filter_types={"file"}):
        uploads = list()
        for info in upload_info:
            # lets be careful with malformed user data
            if not isinstance(info, dict) or not isinstance(info.get("url"), str):
                continue

            upload = temporary_upload_from_url(info["url"])
            if upload:
                uploads.append(upload)

        if uploads:
            result[data_path] = (component, uploads, configuration_path)

    return result


def resize_attachment(
    attachment: SubmissionFileAttachment, size: Tuple[int, int]
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
