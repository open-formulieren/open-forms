from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.authentication.fields import (
    BackendChoiceField as AuthenticationBackendChoiceField,
)
from openforms.authentication.registry import register as auth_register

from . import Form


class FormAuthenticationBackend(models.Model):
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name="auth_backends",
    )
    backend = AuthenticationBackendChoiceField(_("authentication backend"))
    options = models.JSONField(
        _("authentication backend options"),
        encoder=DjangoJSONEncoder,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("authentication backend")
        verbose_name_plural = _("authentication backends")
        constraints = [
            models.UniqueConstraint(
                fields=["form", "backend"],
                name="form_backend_unique_together",
            ),
        ]

    def __str__(self):
        form_str = str(self.form) if self.form_id else _("(unsaved form)")
        return _("{backend} on {form}").format(
            backend=self.get_backend_display(), form=form_str
        )

    def get_backend_display(self):
        if not self.backend or self.backend not in auth_register:
            return _("unknown backend")
        return auth_register[self.backend].verbose_name
