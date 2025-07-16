import hashlib
import os.path
import uuid
from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import TYPE_CHECKING, cast

from django.core.files.base import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from glom import glom
from privates.fields import PrivateMediaFileField

from openforms.typing import JSONValue
from openforms.utils.files import DeleteFileFieldFilesMixin, DeleteFilesQuerySetMixin

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

    def as_form_dict(self) -> Mapping[str, list["SubmissionFileAttachment"]]:
        files = defaultdict(list)
        for file in self:
            files[file._component_configuration_path].append(file)
        return dict(files)


class SubmissionFileAttachmentManager(models.Manager):
    def get_or_create_from_upload(
        self,
        submission_step: SubmissionStep,
        submission_variable: "SubmissionValueVariable",
        configuration_path: str,
        data_path: str,
        upload: TemporaryFileUpload,
        file_name: str | None = None,
    ) -> tuple["SubmissionFileAttachment", bool]:
        try:
            return (
                self.get(
                    submission_step=submission_step,
                    temporary_file=upload,
                    submission_variable=submission_variable,
                    _component_configuration_path=configuration_path,
                    _component_data_path=data_path,
                ),
                False,
            )
        except self.model.DoesNotExist:
            with upload.content.open("rb") as content:
                instance = self.create(
                    submission_step=submission_step,
                    temporary_file=upload,
                    submission_variable=submission_variable,
                    # wrap in File() so it will be physically copied
                    content=File(content, name=upload.file_name),
                    content_type=upload.content_type,
                    original_name=upload.file_name,
                    file_name=file_name,
                    _component_configuration_path=configuration_path,
                    _component_data_path=data_path,
                )
            return (instance, True)


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
    submission_variable = models.ForeignKey(
        verbose_name=_("submission variable"),
        help_text=_("submission value variable for the form component"),
        to="SubmissionValueVariable",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    # The whole path and not just the key is needed for nested fields.
    _component_configuration_path = models.CharField(
        verbose_name=_("component configuration path"),
        help_text=_(
            "Path to the component in the configuration corresponding to this attachment."
        ),
        max_length=255,
        blank=True,
    )
    # Needed to distinguish in which iteration of a repeating group a file was attached
    _component_data_path = models.CharField(
        verbose_name=_("component data path"),
        help_text=_("Path to the attachment in the submission data."),
        max_length=255,
        blank=True,
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

    objects = SubmissionFileAttachmentManager.from_queryset(
        SubmissionFileAttachmentQuerySet
    )()

    class Meta:
        verbose_name = _("submission file attachment")
        verbose_name_plural = _("submission file attachments")
        # see https://docs.djangoproject.com/en/2.2/topics/db/managers/#using-managers-for-related-object-access
        base_manager_name = "objects"

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        return self.file_name or self.original_name

    get_display_name.short_description = _("File name")

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

    def _get_formio_config_property(
        self, lookup: str, default: JSONValue = ""
    ) -> JSONValue:
        """
        Derive a property from the attached formio configuration.
        """
        wrapper = self.submission_step.form_step.form_definition.configuration_wrapper
        component = wrapper.flattened_by_path.get(self._component_configuration_path)
        if not component:
            return None

        if value := glom(component, lookup, default=default):
            # the cast is what *should* happen here, but due to formio shenanigans it is
            # not guaranteed at runtime.
            return cast(JSONValue, value)

        return None

    @property
    def informatieobjecttype(self) -> str:
        """
        Get the informatieobjecttype for this attachment from the configuration
        """
        if (
            value := self._get_formio_config_property(
                "registration.informatieobjecttype"
            )
        ) is not None:
            return str(value)
        return ""

    @property
    def bronorganisatie(self) -> str:
        """
        Get the bronorganisatie for this attachment from the configuration
        """
        if (
            value := self._get_formio_config_property("registration.bronorganisatie")
        ) is not None:
            return str(value)
        return ""

    @property
    def doc_vertrouwelijkheidaanduiding(self) -> str:
        """
        Get the vertrouwelijkheidaanduiding for this attachment from the configuration
        """
        if (
            value := self._get_formio_config_property(
                "registration.docVertrouwelijkheidaanduiding"
            )
        ) is not None:
            return str(value)
        return ""

    @property
    def titel(self) -> str:
        """
        Get the title for this attachment from the configuration
        """
        if (
            value := self._get_formio_config_property("registration.titel")
        ) is not None:
            return str(value)
        return ""

    @property
    def form_key(self):
        if self.submission_variable:
            return self.submission_variable.key
        raise Exception("tried to access an attachment without .submission_variable")

    form_key.fget.short_description = _("form component key")
