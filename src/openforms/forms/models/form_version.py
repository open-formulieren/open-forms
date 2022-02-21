import uuid as _uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class FormVersion(models.Model):
    uuid = models.UUIDField(_("UUID"), unique=True, default=_uuid.uuid4)
    form = models.ForeignKey(
        verbose_name=_("form"),
        to="forms.Form",
        on_delete=models.CASCADE,
    )
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

    class Meta:
        verbose_name = _("form version")
        verbose_name_plural = _("form versions")

    def __str__(self):
        return f"{self.form.admin_name} ({self.created})"
