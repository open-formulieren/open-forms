from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form


class FormVersion(models.Model):
    date_creation = models.DateTimeField(
        verbose_name=_("date of creation"),
        help_text=_("Date and time of creation of the form version."),
        auto_now_add=True,
    )
    form = models.ForeignKey(
        verbose_name=_("form"),
        to=Form,
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
        return f"{self.form.name} ({self.date_creation})"
