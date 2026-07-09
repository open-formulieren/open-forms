from __future__ import annotations

import hashlib
import os.path
import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING, ClassVar

from django.contrib import admin
from django.core.files.base import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from privates.fields import PrivateMediaFileField

from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin
from openforms.variables.constants import FormVariableDataTypes

from .submission import Submission
from .submission_step import SubmissionStep

if TYPE_CHECKING:
    from .submission_value_variable import SubmissionValueVariable

logger = structlog.stdlib.get_logger(__name__)


def fmt_upload_to(prefix, instance, filename):
    name, ext = os.path.splitext(filename)
    return "{p}/{d}/{u}{e}".format(
        p=prefix, d=date.today().strftime("%Y/%m/%d"), u=instance.uuid, e=ext
    )


def temporary_file_upload_to(instance, filename):
    return fmt_upload_to("temporary-uploads", instance, filename)


def submission_file_upload_to(instance, filename):
    return fmt_upload_to("submission-uploads", instance, filename)


class TemporaryFileUploadQuerySet(DeleteFilesQuerySetMixin, models.QuerySet):
    def select_prune(self, age: timedelta):
        return self.filter(created_on__lt=timezone.now() - age)


class TemporaryFileUpload(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("Submission the temporary file upload belongs to."),
    )
    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to=temporary_file_upload_to,
        help_text=_("content of the file attachment."),
    )
    file_name = models.CharField(_("original name"), max_length=255)
    content_type = models.CharField(_("content type"), max_length=255)
    # store the file size to not have to do disk IO to get the file size
    file_size = models.PositiveIntegerField(
        _("file size"),
        default=0,
        help_text=_("Size in bytes of the uploaded file."),
    )
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)

    objects = TemporaryFileUploadQuerySet.as_manager()

    class Meta:
        verbose_name = _("temporary file upload")
        verbose_name_plural = _("temporary file uploads")

    def __str__(self):
        return self.file_name


class SubmissionFileAttachmentQuerySet(
    DeleteFilesQuerySetMixin, models.QuerySet["SubmissionFileAttachment"]
):
    def for_submission(self, submission: Submission):
        return self.filter(submission_step__submission=submission)


class SubmissionFileAttachmentManager(models.Manager["SubmissionFileAttachment"]):
    def get_or_create_from_upload(
        self,
        upload: TemporaryFileUpload,
        *,
        submission_step: SubmissionStep,
        submission_variable: SubmissionValueVariable,
        file_component_key: str,
        data_path: str,
        file_name: str,
    ) -> tuple[SubmissionFileAttachment, bool]:
        """
        Look up or create the submission file attachment for a given temporary upload.

        A temporary upload always maps one-to-one with a submission file attachment,
        even if the file is uploaded multiple times (in those cases, every copy will
        be stored in its own temporary upload).

        :param upload: The temporary upload from which the content will be copied into
          the persisted submission file attachment.

        :param submission_step: The submission step where the upload happened. Together
          with the submission variable, the associated formio form definition and
          :arg:`file_component_key`, the file component leading to the upload can be
          resolved.

        :param submission_variable: The submission variable that holds the raw formio
          value as submitted by the end-user. It's a result of saving the submission
          step data.

          .. note:: When the file component is in an editgrid, there is no variable for
             the file component itself, and instead the submission variable points to
             the editgrid closest to the configuration root, even with nested edit
             grids.

        :param file_component_key: Formio component key of the file component that
          produced the upload. It does not contain any editgrid ancestor keys, and it
          may contain ``.`` characters if that's what the form designer entered for the
          key. Currently relies on the implementation detail that Open Forms enforces
          unique component keys even for components inside edit grid definitions.

        :param data_path: Dotted path into the submission data object structure,
          pointing out to which exact field this upload belongs. It's always populated,
          and outside of editgrids it's identical to the submission variable key. Inside
          editgrids, it contains indices pointing out the item in the edit grid, e.g.
          ``editgrid.3.someFile`` points to the fourth item in the edit grid, with
          ``someFile`` the value of the :arg:`file_component_key`.

        :param file_name: The name of the file after server-side processing. The
          original file name will be stored as well, after taking it from the temporary
          upload.

        :returns: A tuple of the retrieved or created model instance and a bool
          indicating whether the record was created.
        """

        # if it's not an edit grid variable, the submission variable key should match
        # the component key value
        assert (
            submission_variable.data_type == FormVariableDataTypes.array
            and submission_variable.data_subtype == FormVariableDataTypes.editgrid
        ) or (submission_variable.key == file_component_key), (
            "The wrong variable or file component key is passed!"
        )
        # also check against the snapshot of the configuration - this mostly catches
        # inconsistencies in the test suite since asserts don't run in production
        assert (
            submission_variable.configuration
            and submission_variable.configuration.get("type") in ("file", "editgrid")
        ), (
            "The component configuration snapshot does not meet file-component expectations"
        )

        # the one-to-one field contains a unique constraint with the temporary
        # upload. The additional fields are included in the query so that bugs surface
        # early in the form of an integrity error when trying to create the attachment
        # with the wrong metadata.
        try:
            existing_attachment = self.get(
                temporary_file=upload,
                submission_step=submission_step,
                submission_variable=submission_variable,
                component_key=file_component_key,
                _data_path=data_path,
            )
            return (existing_attachment, False)
        except self.model.DoesNotExist:
            with upload.content.open("rb") as content:
                instance = self.create(
                    temporary_file=upload,
                    submission_step=submission_step,
                    submission_variable=submission_variable,
                    # wrap in File() so it will be physically copied
                    content=File(content, name=upload.file_name),
                    content_type=upload.content_type,
                    original_name=upload.file_name,
                    file_name=file_name,
                    component_key=file_component_key,
                    _data_path=data_path,
                )
            return (instance, True)

    if TYPE_CHECKING:

        def for_submission(
            self, submission: Submission
        ) -> SubmissionFileAttachmentQuerySet: ...


class SubmissionFileAttachment(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission_step = models.ForeignKey(
        to="SubmissionStep",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("Submission step the file is attached to."),
        related_name="attachments",
    )
    temporary_file = models.OneToOneField(
        to="TemporaryFileUpload",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("temporary file"),
        help_text=_("Temporary upload this file is sourced to."),
        related_name="attachment",
    )
    submission_variable = models.ForeignKey(
        verbose_name=_("submission variable"),
        help_text=_("submission value variable for the form component"),
        to="SubmissionValueVariable",
        on_delete=models.CASCADE,
    )
    # DeprecationWarning: replaced by the component_key field and data is migrated in
    # 4.0. We're keeping this field around "just in case" and will drop it in 4.1 at the
    # earliest.
    _component_configuration_path = models.CharField(
        verbose_name=_("component configuration path"),
        help_text=_(
            "Path to the component in the configuration corresponding to this attachment."
        ),
        max_length=255,
        blank=True,
    )
    # _data_path and _component_key allow us to match the upload with the submission
    # data, which is necessary for registration plugins and submission post-processing.
    # Note that the _component_key semantics rely on our frontend enforcing unique keys
    # in a form, even when the file component is inside an editgrid (something that is
    # not necessary) - this is however currently required and relied on for registration
    # options for files, so if this behaviour changes, don't forget about that code!
    # XXX: would be nice we can drop this global-uniqueness requirement, but then we
    # have to store abstract data paths (editgrid item paths without the actual
    # iteration identifiers -> editgrid.$i.file becomes editgrid.file, like
    # formio conditionals).

    # TODO: should probably be TextField to be future proof
    _data_path = models.CharField(
        verbose_name=_("component data path"),
        help_text=_("Path to the attachment in the submission data."),
        max_length=255,
        blank=True,
    )
    component_key = models.TextField(
        _("component key"),
        help_text=_(
            "Key of the file component for which the upload was made. Most of the time "
            "this will be identical to the submission_variable.key, except when the "
            "file component is inside an edit grid - the variable then points to the "
            "edit grid."
        ),
    )

    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to=submission_file_upload_to,
        help_text=_("Content of the submission file attachment."),
    )
    file_name = models.CharField(
        _("file name"), max_length=255, help_text=_("reformatted file name"), blank=True
    )
    original_name = models.CharField(
        _("original name"), max_length=255, help_text=_("original uploaded file name")
    )
    content_type = models.CharField(_("content type"), max_length=255)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        SubmissionFileAttachmentManager
    ] = SubmissionFileAttachmentManager.from_queryset(
        SubmissionFileAttachmentQuerySet
    )()

    class Meta:
        verbose_name = _("submission file attachment")
        verbose_name_plural = _("submission file attachments")
        base_manager_name = "objects"
        constraints = [
            models.CheckConstraint(
                name="required_non_empty_component_metadata",
                condition=~(models.Q(_data_path="") | models.Q(component_key="")),
            ),
        ]

    def __str__(self):
        return self.get_display_name()

    @admin.display(description=_("File name"))
    def get_display_name(self):
        return self.file_name or self.original_name

    @property
    def content_hash(self) -> str:
        """
        Calculate the sha256 hash of the content.

        MD5 is fast, but has known collisions, so we use sha256 instead.
        """
        chunk_size = 8192
        sha256 = hashlib.sha256()
        with self.content.open(mode="rb") as file_content:
            while chunk := file_content.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    @property
    def data_path(self) -> str:
        """
        Fully qualified data path to the Formio component value.

        The data path points from the root of the submission data object to the leaf
        node (FileComponent) value. It is necessary to know which attachments belong to
        which item in an editgrid (repeating group). For file components *not* in an
        edit grid, the data path is effectivley identical to the key of the submission
        variable the attachment belongs to, which is linked to the file component
        itself.

        Example values:

        * ``"myFile"`` - points to a file component in the root or inside a layout
          component like fieldset or columns. Note that the keys of layout components
          are not part of the data path.
        * ``"parent.myFile"`` - inside a nested data structure, because a period is used
          in the file component key
        * ``editgrid.3.someFile`` - points to a file component used in the fourth item
          in an edit grid. Note that editgrids could be nested, and that in theory it's
          also possible this is not an editgrid, but a hardcoded key with this number,
          which *also* creates a nested datastructure:
          ``{"editgrid": {"3": {"someFile": []}}}`` (this is cursed).
        """
        return self._data_path
