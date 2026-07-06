import os.path
import pathlib
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from typing import Annotated
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.urls import Resolver404, resolve
from django.utils.translation import gettext as _

import PIL
import structlog
from glom import glom
from PIL import Image

from openforms.api.exceptions import RequestEntityTooLarge
from openforms.conf.utils import Filesize
from openforms.formio.service import (
    FormioData,
    holds_submission_data,
    iter_components,
)
from openforms.formio.typing import (
    Component,
    EditGridComponent,
    FileComponent,
    FileValue,
)
from openforms.submissions.models import (
    Submission,
    SubmissionFileAttachment,
    SubmissionStep,
    TemporaryFileUpload,
)
from openforms.template import render_from_string, sandbox_backend
from openforms.variables.service import resolve_key

from .metrics import upload_file_size

__all__ = ["process_step_uploads", "iter_and_persist_step_uploads"]

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
    index: Annotated[int, "one-based"]
    num_uploads: int
    data_path: str  # The path to the component data in the submission data
    component: FileComponent


def process_step_uploads(step: SubmissionStep) -> None:
    """
    Exhaust the generator that does the actual upload processing.
    """
    for __ in iter_and_persist_step_uploads(step):
        pass


def iter_and_persist_step_uploads(
    submission_step: SubmissionStep,
) -> Iterator[tuple[SubmissionFileAttachment, bool]]:
    """
    Persist the user uploads in the step submission data.

    The raw Formio component values for file uploads are extracted, matching the values
    with the temporary uploads stored in the database. Each temporary upload is resolved
    against the specific file upload field/component, persisted and related to the
    matching submission step and variable.

    Image uploads are scheduled on the background tasks queue for post-processing to
    ensure they're resized if image resizing is requested.
    """
    assert submission_step.form_step is not None
    submission = submission_step.submission
    assert isinstance(submission, Submission)  # type narrowing
    execution_state = submission.load_execution_state()
    variable_state = submission.variables_state
    step_variables = variable_state.get_variables_in_submission_step(submission_step)
    # evaluate the collection once outside loop
    step_variables_keys = list(step_variables.keys())

    for upload_context in resolve_uploads_in_step(submission_step):
        upload, component = upload_context.upload, upload_context.component

        # check file size limits - this can only be performed once we have the link
        # between the component (holding the configuration) and the temporary upload (
        # which has the actual current size of the file)
        file_max_size = file_size_cast(
            glom(component, "fileMaxSize", default="") or settings.MAX_FILE_UPLOAD_SIZE
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

        # all good - now build up the (remaining) metadata to persist the file to disk
        # and database
        variable_key = resolve_key(upload_context.data_path, step_variables_keys)
        assert variable_key is not None, "The upload must be related to a variable"
        submission_variable = step_variables[variable_key]

        # calculate the final file name, taking into account configuration on the
        # component which may use template expressions
        base_name = render_from_string(
            source=glom(component, "file.name", default=""),
            context={"fileName": pathlib.Path(upload.file_name).stem},
            backend=sandbox_backend,
        )
        file_name = append_file_num_postfix(
            upload.file_name,
            base_name,
            upload_context.index,
            upload_context.num_uploads,
        )

        # and finally, persist it all
        (
            attachment,
            created,
        ) = SubmissionFileAttachment.objects.get_or_create_from_upload(
            upload,
            submission_step=submission_step,
            submission_variable=submission_variable,
            file_component_key=component["key"],
            data_path=upload_context.data_path,
            file_name=file_name,
        )
        yield (attachment, created)
        if created:
            _maybe_schedule_resize(attachment.pk, component)

        # update OTel metric
        current_step_index = execution_state.get_step_index(
            submission_step.form_step.uuid
        )
        upload_file_size.record(
            attachment.content.size,
            attributes={
                "openforms.form.name": submission_step.submission.form.name,
                "openforms.form.uuid": str(submission_step.submission.form.uuid),
                "openforms.step.name": submission_step.form_step.form_definition.name,
                "openforms.step.number": current_step_index + 1,
                "content_type": attachment.content_type,
            },
        )
        logger.info(
            "attachment_added",
            content_type=attachment.content_type,
            file_size=attachment.content.size,
        )


def _maybe_schedule_resize(attachment_pk: int, component: FileComponent) -> None:
    # circular import
    from .tasks import resize_submission_attachment

    # grab resize settings
    resize_apply = glom(component, "of.image.resize.apply", default=False)
    resize_size = (
        glom(component, "of.image.resize.width", default=DEFAULT_IMAGE_MAX_SIZE[0]),
        glom(component, "of.image.resize.height", default=DEFAULT_IMAGE_MAX_SIZE[1]),
    )
    if not resize_apply or not resize_size:
        return

    # NOTE there is a possible race-condition if user completes a submission before this resize task is done
    # see https://github.com/open-formulieren/open-forms/issues/507
    transaction.on_commit(
        partial(resize_submission_attachment.delay, attachment_pk, resize_size)
    )


def cleanup_submission_temporary_uploaded_files(submission: Submission):
    for attachment in SubmissionFileAttachment.objects.for_submission(
        submission
    ).filter(temporary_file__isnull=False):
        attachment.temporary_file.delete()


def cleanup_unclaimed_temporary_uploaded_files(age=timedelta(days=2)):
    for file in TemporaryFileUpload.objects.select_prune(age).filter(attachment=None):
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


def _resolve_uploads_in_component(
    component: Component,
    data: FormioData,
    parent_data_path: str = "",
) -> Iterator[UploadContext]:
    """
    Process the uploads in a single formio component, recurse if necessary.

    We only recurse into edit grids, callers must ensure that they process the layout
    component children too.
    """
    from typing import cast  # noqa: TID251

    # there's no point in processing layout components. The caller is responsible for
    # invoking some form of `iter_components` to ensure the layout component children
    # get processed too.
    # TODO: this will be refactored in the msgspec branch with a proper tree processing
    # library.
    if not holds_submission_data(component):
        return

    # we're only interested in file components (and editgrids, to recurse into)
    if component["type"] not in ("file", "editgrid"):
        return

    # narrowing does not work out of the box, so we must use the forbidden cast...
    # TODO: will be resolved in the msgspec branch
    component = cast(FileComponent | EditGridComponent, component)

    # if we're in some kind of recursion depth, ensure to add the parent path prefix for
    # a fully qualified data path from the root to the leaf node(s)
    data_path = component["key"]
    if parent_data_path:
        data_path = f"{parent_data_path}.{data_path}"

    match component:
        # when we have a file component itself (not in an edit grid), processing
        # is pretty straight forward
        case {"type": "file"}:
            component = cast(FileComponent, component)  # can't assert with TypedDict
            files: FileValue = data.get(data_path, [])
            uploads: Sequence[TemporaryFileUpload] = [
                upload
                for file in files
                if (upload := temporary_upload_from_url(file.get("url"))) is not None
            ]
            num_uploads = len(uploads)
            for i, upload in enumerate(uploads, start=1):
                yield UploadContext(
                    upload=upload,
                    index=i,
                    num_uploads=num_uploads,
                    component=component,
                    data_path=data_path,
                )

        # in editgrids, recurse and build up the parent path prefix
        case {"type": "editgrid"}:
            component = cast(
                EditGridComponent, component
            )  # can't assert with TypedDict
            # hidden/cleared edit grids are typically completely absent from the
            # submission data
            if data_path not in data:
                return

            items = data[data_path]
            assert isinstance(items, list)

            # extract the children once to process them for each item (recursively)
            editgrid_components = list(
                iter_components(
                    component,
                    recursive=True,
                    recurse_into_editgrid=False,
                )
            )

            for index, item in enumerate(items):
                assert isinstance(item, dict)
                for nested in editgrid_components:
                    yield from _resolve_uploads_in_component(
                        nested,
                        data,
                        parent_data_path=f"{data_path}.{index}",
                    )

        case _:  # pragma: no cover
            raise ValueError("Component type should not have been let through.")


def resolve_uploads_in_step(submission_step: SubmissionStep) -> Iterator[UploadContext]:
    """
    Extract the file uploads from the Submission step data (Formio data).

    Loop over all the file components in the form step definition/configuration, and
    grab the Formio for each component. When data is present, process the Formio object
    and resolve the temporary file upload that was created.

    This resolution process takes care of properly prefixing the data paths when file
    uploads are contained in (nested) edit grids, so that:

    * we can process the file uploads during registration and look them up from the
      variables again
    * we can resolve the component definition that the upload belongs to again, so that
      we can apply component-specific configuration where necessary.

    The Formio upload data looks like the shape below:

    .. code-block:: json

        {"my_file": [
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
        ]}
    """
    assert submission_step.form_step is not None
    assert isinstance(submission_step.submission, Submission)
    state = submission_step.submission.variables_state
    data = state.get_data(submission_step=submission_step, include_unsaved=False)
    configuration = submission_step.form_step.form_definition.configuration

    # we're doing the looping manually here because our data structures aren't good
    # enough:
    # * FormioConfigurationWrapper *does* recurse into editgrids, which we don't want
    #   at this point
    # * FormioConfigurationWrapper also does not keep track of the parent
    #   paths/components, and we want to process editgrids as we encounter them to
    #   inject the item indices into the data paths to resolve the uploads, but keep
    #   them out of the metadata when saving this to the DB so that later on we can
    #   still resolve the component without any guesswork
    for component in iter_components(
        configuration,
        recursive=True,
        recurse_into_editgrid=False,
    ):
        yield from _resolve_uploads_in_component(component, data)


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
