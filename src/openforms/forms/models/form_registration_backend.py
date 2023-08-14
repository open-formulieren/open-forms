from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.registrations.fields import RegistrationBackendChoiceField
from openforms.registrations.registry import register as registration_register
from openforms.typing import RegistrationBackendKey

from . import Form


class FormRegistrationBackend(models.Model):
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name="registration_backends",
    )
    key: RegistrationBackendKey = models.CharField(
        _("key"),
        max_length=50,
        help_text=_("The key to use to refer to this configuration in form logic."),
    )
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("A recognisable name for this backend configuration."),
    )
    backend = RegistrationBackendChoiceField(_("registration backend"))
    options = models.JSONField(
        _("registration backend options"),
        default=dict,
        blank=True,
    )

    class Meta:
        unique_together = ("form", "key")
        verbose_name = _("registration backend")
        verbose_name_plural = _("registration backends")

    def __str__(self):
        return _("{backend} on {form}").format(backend=self.name, form=self.form)

    def get_backend_display(self):
        choices = dict(registration_register.get_choices())
        return choices.get(
            self.backend,
            "-",
        )

    get_backend_display.short_description = _("registration backend")
