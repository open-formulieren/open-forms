import uuid as _uuid

from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.utils.fields import StringUUIDField


class FormVersion(models.Model):
    uuid = StringUUIDField(_("UUID"), unique=True, default=_uuid.uuid4)

    created = models.DateTimeField(
        verbose_name=_("created"),
        help_text=_("Date and time of creation of the form version."),
        auto_now_add=True,
    )
    form = models.ForeignKey(
        verbose_name=_("form"),
        to="forms.Form",
        on_delete=models.CASCADE,
    )
    export_blob = JSONField(
        help_text=_(
            "The form, form definitions and form steps that make up this version, saved as JSON data."
        ),
    )

    class Meta:
        verbose_name = _("form version")
        verbose_name_plural = _("form versions")

    def __str__(self):
        return f"{self.form.name} ({self.created})"
