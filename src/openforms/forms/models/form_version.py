from __future__ import annotations

import uuid as _uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.formats import localize
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from .form import Form

if TYPE_CHECKING:
    from ..import_export.service import Artifact

User = get_user_model()


def get_version_export_blob(form: Form) -> Mapping[str, str]:
    """
    Get the export blob as plain strings rather than bytestrings.

    The default export artifact encoding behaviour is to emit bytestrings, but those
    can't be stored out-of-the-box in a ``models.JSONField``, so we convert those back
    to plain strings. msgspec outputs utf-8 bytestrings.

    # FIXME: see comment on model field
    """
    # circular dependencies
    from ..import_export.service import (
        AdditionalFormConfigurationOptions,
        FormConfigurationOptions,
        FormExportOptions,
        get_export_artifact,
    )

    artifact = get_export_artifact(
        form,
        export_options=FormExportOptions(
            form_configuration=[
                FormConfigurationOptions.registration_backends,
                FormConfigurationOptions.prefill,
                FormConfigurationOptions.payment_backend,
                FormConfigurationOptions.auth_backends,
            ],
            additional_form_configuration=[
                AdditionalFormConfigurationOptions.product,
                AdditionalFormConfigurationOptions.wms_tile_layers,
                AdditionalFormConfigurationOptions.wmts_tile_layers,
                AdditionalFormConfigurationOptions.yivi_attribute_groups,
            ],
            remove_sensitive_content=False,
        ),
    )
    resources = artifact.as_resources_mapping(encode=True)
    return {key: value.decode() for key, value in resources.items()}


class FormVersionManager(models.Manager["FormVersion"]):
    def create_for(
        self, form: Form, description="", user: AbstractBaseUser | None = None
    ) -> FormVersion:
        """
        Create a new ``FormVersion`` record for a given form.
        """
        if not description:
            version_number = self.filter(form=form).count() + 1
            description = _("Version {number}").format(number=version_number)
        return self.create(
            form=form,
            export_blob=get_version_export_blob(form),
            user=user,
            description=description,
        )


def get_app_release():
    return settings.RELEASE or ""


def get_app_git_sha():
    return settings.GIT_SHA or ""


class FormVersion(models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        verbose_name=_("form"),
        to="forms.Form",
        on_delete=models.CASCADE,
    )
    # TODO: ensure we store plain JSON and not double-encoded stuff - this requires the
    # version restore to be adapted though, and the factory model must be updated too
    export_blob = models.JSONField(
        help_text=_(
            "The form, form definitions and form steps that make up this version, saved as JSON data."
        ),
    )
    created = models.DateTimeField(
        verbose_name=_("created"),
        help_text=_("Date and time of creation of the form version."),
        auto_now_add=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("user"),
        help_text=_("User who authored this version."),
    )
    description = models.TextField(
        _("version description"),
        blank=True,
        help_text=_("Description/context about this particular version."),
    )
    app_release = models.CharField(
        _("application version"),
        max_length=50,
        blank=True,
        help_text=_("App release/version at the time this version was created."),
        editable=False,
        default=get_app_release,
    )
    app_git_sha = models.CharField(
        _("application commit hash"),
        max_length=50,
        blank=True,
        help_text=_("Application commit hash at the time this version was created."),
        editable=False,
        default=get_app_git_sha,
    )

    objects: ClassVar[FormVersionManager] = FormVersionManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        verbose_name = _("form version")
        verbose_name_plural = _("form versions")

    def __str__(self):
        timestamp = localize(localtime(self.created))
        return f"{self.form.admin_name} ({timestamp})"

    def get_import_artifact(self) -> Artifact:
        from ..import_export.service import Artifact

        return Artifact.from_raw_data(self.export_blob, needs_decode=True)
