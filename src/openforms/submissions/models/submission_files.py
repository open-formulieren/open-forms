import hashlib
import logging
import os.path
import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Mapping, Optional, Tuple

from django.core.files.base import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from privates.fields import PrivateMediaFileField

from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin

from .submission import Submission
from .submission_step import SubmissionStep

logger = logging.getLogger(__name__)


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


class SubmissionFileAttachmentQuerySet(DeleteFilesQuerySetMixin, models.QuerySet):
    def for_submission(self, submission: Submission):
        return self.filter(submission_step__submission=submission)

    def as_form_dict(self) -> Mapping[str, List["SubmissionFileAttachment"]]:
        files = defaultdict(list)
        for file in self:
            files[file.form_key].append(file)
        return dict(files)


class SubmissionFileAttachmentManager(models.Manager):
    def create_from_upload(
        self,
        submission_step: SubmissionStep,
        form_key: str,
        upload: TemporaryFileUpload,
        file_name: Optional[str] = None,
    ) -> Tuple["SubmissionFileAttachment", bool]:
        try:
            return (
                self.get(
                    submission_step=submission_step,
                    temporary_file=upload,
                    form_key=form_key,
                ),
                False,
            )
        except self.model.DoesNotExist:
            return (
                self.create(
                    submission_step=submission_step,
                    temporary_file=upload,
                    form_key=form_key,
                    # wrap in File() so it will be physically copied
                    content=File(upload.content, name=upload.file_name),
                    content_type=upload.content_type,
                    original_name=upload.file_name,
                    file_name=file_name,
                ),
                True,
            )


class SubmissionFileAttachment(DeleteFileFieldFilesMixin, models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission_step = models.ForeignKey(
        to="SubmissionStep",
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_("Submission step the file is attached to."),
        related_name="attachments",
    )
    # TODO OneToOne?
    temporary_file = models.ForeignKey(
        to="TemporaryFileUpload",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("temporary file"),
        help_text=_("Temporary upload this file is sourced to."),
        related_name="attachments",
    )
    form_key = models.CharField(_("form component key"), max_length=255)

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

    objects = SubmissionFileAttachmentManager.from_queryset(
        SubmissionFileAttachmentQuerySet
    )()

    class Meta:
        verbose_name = _("submission file attachment")
        verbose_name_plural = _("submission file attachments")
        # see https://docs.djangoproject.com/en/2.2/topics/db/managers/#using-managers-for-related-object-access
        base_manager_name = "objects"

    def get_display_name(self):
        return self.file_name or self.original_name

    def get_format(self):
        return os.path.splitext(self.get_display_name())[1].lstrip(".")

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
